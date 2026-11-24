
import os
import statistics
from sqlalchemy.orm import Session as DBSession

import models
from services.audio_extractor import extract_audio_from_video
from services.transcriber import transcribe_audio
from services.speech_analyser import analyse_speech
from services.content_analyser import analyse_content
from services.video_analyser import analyse_video
from services.feedback_generator import generate_feedback


def run_analysis_pipeline(session_id: int, user_id: int, db: DBSession):
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        raise ValueError(f"Session {session_id} not found")

    answers = db.query(models.SessionAnswer).filter(
        models.SessionAnswer.session_id == session_id
    ).all()

    per_answer_content = []
    per_answer_fluency = []
    per_answer_nonverbal = []

    agg_speech_metrics = {}
    agg_nonverbal_metrics = {}
    agg_content_metrics = {}

    # FIX: store authenticity data in plain Python lists — NOT on ORM objects.
    # Storing on ORM objects (answer.is_speaking, answer.visual_speaking) fails
    # because these are not real DB columns. After db.commit() SQLAlchemy expires
    # all objects and trying to read them back raises InvalidRequestError, which
    # silently kills the pipeline before AnalysisResult is ever created.
    authenticity_scores = []

    for answer in answers:
        video_path = answer.video_path
        if not video_path or not os.path.exists(video_path):
            # No video — treat as neither speaking nor visually speaking
            authenticity_scores.append(0.0)
            continue

        # Step 1: Extract audio
        audio_path = extract_audio_from_video(video_path)
        answer.audio_path = audio_path

        # Step 2: Transcribe — returns (transcript, duration, is_speaking)
        transcript, duration, is_speaking = transcribe_audio(audio_path)
        answer.transcript = transcript
        answer.duration_seconds = duration
        # Do NOT set answer.is_speaking — not a DB column

        # Step 3: Speech/fluency analysis
        speech_result = analyse_speech(audio_path, transcript)

        # Step 4: Content/NLP analysis
        content_result = analyse_content(
            transcript=transcript,
            question_text=answer.question_text,
        )

        # Step 5: Video/nonverbal analysis
        nonverbal_result = analyse_video(video_path)
        visual_speaking = nonverbal_result.get("visual_speaking", False)
        # Do NOT set answer.visual_speaking — not a DB column

        # Persist per-answer scores (these ARE real columns)
        answer.fluency_score = speech_result.get("fluency_score", 0.0)
        answer.content_score = content_result.get("content_score", 0.0)
        answer.nonverbal_score = nonverbal_result.get("nonverbal_score", 0.0)

        per_answer_content.append(answer.content_score)
        per_answer_fluency.append(answer.fluency_score)
        per_answer_nonverbal.append(answer.nonverbal_score)

        # Collect authenticity data right here, while values are in local scope
        if is_speaking and visual_speaking:
            authenticity_scores.append(1.0)
        elif is_speaking and not visual_speaking:
            authenticity_scores.append(0.1)
        elif not is_speaking and visual_speaking:
            authenticity_scores.append(0.2)
        else:
            authenticity_scores.append(0.0)

        # Merge metrics for aggregation
        _merge(agg_speech_metrics, speech_result)
        _merge(agg_nonverbal_metrics, nonverbal_result)
        _merge(agg_content_metrics, content_result)

    # Commit per-answer scores to DB (transcript, duration, fluency, content, nonverbal)
    db.commit()

    # ── AUTHENTICITY CHECK ────────────────────────────────────────────────────
    authenticity_factor = (
        sum(authenticity_scores) / len(authenticity_scores)
        if authenticity_scores else 1.0
    )
    cheating_detected = authenticity_factor < 0.5

    # ── Aggregate session-level scores ────────────────────────────────────────
    content_score   = _safe_mean(per_answer_content)
    fluency_score   = _safe_mean(per_answer_fluency)
    nonverbal_score = _safe_mean(per_answer_nonverbal)

    # Apply authenticity penalty to nonverbal and overall
    nonverbal_score = round(nonverbal_score * authenticity_factor, 1)
    overall_score   = round(
        (0.4 * content_score + 0.35 * fluency_score + 0.25 * nonverbal_score)
        * authenticity_factor,
        1,
    )

    session.content_score   = content_score
    session.fluency_score   = fluency_score
    session.nonverbal_score = nonverbal_score
    session.overall_score   = overall_score
    db.commit()

    # ── Deltas vs previous completed session ──────────────────────────────────
    prev = (
        db.query(models.Session)
        .filter(
            models.Session.user_id == user_id,
            models.Session.completed == True,
            models.Session.id != session_id,
            models.Session.overall_score.isnot(None),
        )
        .order_by(models.Session.created_at.desc())
        .first()
    )

    delta_overall   = round(overall_score   - prev.overall_score,   1) if prev else None
    delta_content   = round(content_score   - prev.content_score,   1) if prev and prev.content_score   else None
    delta_fluency   = round(fluency_score   - prev.fluency_score,   1) if prev and prev.fluency_score   else None
    delta_nonverbal = round(nonverbal_score - prev.nonverbal_score, 1) if prev and prev.nonverbal_score else None

    # ── Generate feedback ─────────────────────────────────────────────────────
    ai_feedback = generate_feedback(
        content_score=content_score,
        fluency_score=fluency_score,
        nonverbal_score=nonverbal_score,
        speech_metrics=agg_speech_metrics,
        nonverbal_metrics=agg_nonverbal_metrics,
        content_metrics=agg_content_metrics,
        cheating_detected=cheating_detected,
    )

    # ── Persist AnalysisResult ────────────────────────────────────────────────
    result = models.AnalysisResult(
        session_id=session_id,
        speech_metrics=agg_speech_metrics,
        nonverbal_metrics=agg_nonverbal_metrics,
        content_metrics=agg_content_metrics,
        delta_overall=delta_overall,
        delta_content=delta_content,
        delta_fluency=delta_fluency,
        delta_nonverbal=delta_nonverbal,
        ai_feedback=ai_feedback,
    )
    db.add(result)
    db.commit()

    print(f"[ORION] Pipeline complete — session {session_id} | score={overall_score}")
    return overall_score


def _safe_mean(values):
    clean = [v for v in values if v is not None]
    return round(statistics.mean(clean), 1) if clean else 0.0


def _merge(base: dict, new: dict):
    """Append values to lists in base dict for later aggregation."""
    for k, v in new.items():
        if isinstance(v, (int, float)):
            base.setdefault(k, []).append(v)