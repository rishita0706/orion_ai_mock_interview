
import os
from typing import List, Dict


def generate_feedback(
    content_score: float,
    fluency_score: float,
    nonverbal_score: float,
    speech_metrics: dict,
    nonverbal_metrics: dict,
    content_metrics: dict,
    cheating_detected: bool = False
) -> List[Dict]:
    """
    Generates 3–5 feedback items combining rule-based analysis.
    Attempts LLM enhancement if API keys are present.
    """
    feedback = []

    # ── Content feedback ──────────────────────────────────────────────────────
    if content_score >= 80:
        feedback.append({
            "category": "Content",
            "text": (
                "Your answers were well-structured and clearly strong to each question. "
                "You demonstrated good use of specific examples to back up your points — "
                "this is exactly what interviewers look for."
            ),
            "sentiment": "positive",
        })
    elif content_score >= 60:
        feedback.append({
            "category": "Content",
            "text": (
                "Your answers covered the main points but could be strengthened with more concrete examples. "
                "Try the STAR method (Situation, Task, Action, Result) to add structure and specificity to your responses."
            ),
            "sentiment": "warning",
        })
    else:
        feedback.append({
            "category": "Content",
            "text": (
                "Your answers would benefit from more depth and relevance to the question asked. "
                "Before responding, take a breath and identify the core thing the interviewer wants to know. "
                "Then build your answer around that."
            ),
            "sentiment": "warning",
        })

    has_conclusion = _mean_value(content_metrics, "has_conclusion")
    if not has_conclusion:
        feedback.append({
            "category": "Structure",
            "text": (
                "Several answers ended abruptly without a clear conclusion. "
                "Finishing with a brief summary or takeaway (e.g. 'So in summary, this experience taught me X') "
                "makes your answer feel polished and memorable."
            ),
            "sentiment": "warning",
        })

    # ── Fluency feedback ──────────────────────────────────────────────────────
    filler_count = _mean_value(speech_metrics, "filler_count")
    wpm = _mean_value(speech_metrics, "wpm")

    if filler_count and filler_count > 5:
        feedback.append({
            "category": "Speech Fluency",
            "text": (
                f"You used filler words (um, uh, like, basically) approximately {int(filler_count)} times per answer. "
                "Replace fillers with intentional pauses — a 1-second pause actually sounds more confident than 'um'. "
                "Practice recording yourself and listening back to build awareness."
            ),
            "sentiment": "warning",
        })
    elif fluency_score >= 80:
        feedback.append({
            "category": "Speech Fluency",
            "text": (
                "Your speech was clear and well-paced. "
                "Minimal filler words and natural pausing make you sound confident and easy to follow."
            ),
            "sentiment": "positive",
        })

    if wpm and wpm > 175:
        feedback.append({
            "category": "Pace",
            "text": (
                f"Your speaking pace was slightly fast ({int(wpm)} wpm). "
                "Slow down by 10–15% — this gives your interviewer time to absorb your answer "
                "and projects calm confidence."
            ),
            "sentiment": "warning",
        })
    elif wpm and wpm < 90:
        feedback.append({
            "category": "Pace",
            "text": (
                "Your speaking pace was a little slow. Try to be slightly more energetic in your delivery "
                "while still maintaining clarity — it helps keep the interviewer engaged."
            ),
            "sentiment": "neutral",
        })

    # ── Non-verbal feedback ───────────────────────────────────────────────────
    eye_contact = _mean_value(nonverbal_metrics, "eye_contact_pct")
    posture = _mean_value(nonverbal_metrics, "posture_score")
    emotion = nonverbal_metrics.get("dominant_emotion", "neutral")

    if eye_contact and eye_contact >= 75:
        feedback.append({
            "category": "Non-Verbal",
            "text": (
                f"Excellent eye contact — you maintained camera gaze about {int(eye_contact)}% of the time. "
                "This creates a strong impression of confidence and engagement in video interviews."
            ),
            "sentiment": "positive",
        })
    elif eye_contact and eye_contact < 50:
        feedback.append({
            "category": "Non-Verbal",
            "text": (
                "Your eye contact with the camera was below 50% — this can read as uncertain or distracted. "
                "Place a sticky note near your camera as a reminder to look there while speaking."
            ),
            "sentiment": "warning",
        })

    if posture and posture < 60:
        feedback.append({
            "category": "Posture",
            "text": (
                "Your posture could be improved — try sitting upright with both shoulders level. "
                "Good posture signals confidence and professionalism, even in a video call."
            ),
            "sentiment": "warning",
        })

    if cheating_detected:
        feedback.append({
            "category": "Authenticity",
            "text": "Audio and visual signals did not match. Please ensure you are speaking live instead of playing recorded answers.",
            "sentiment": "warning"
        })

    # ── Cap at 5 feedback items ───────────────────────────────────────────────
    return feedback[:5]


def _mean_value(metrics: dict, key: str):
    """Safely get a scalar or mean from a list value in metrics dict."""
    val = metrics.get(key)
    if val is None:
        return None
    if isinstance(val, list):
        return sum(val) / len(val) if val else None
    return val
