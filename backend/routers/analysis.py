
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from typing import Optional, List, Any
from database import get_db
from routers.auth import get_current_user
import models

router = APIRouter()


class FeedbackItem(BaseModel):
    category: str
    text: str
    sentiment: str  # "positive" | "warning" | "neutral"


class AnalysisOut(BaseModel):
    session_id: int
    overall_score: Optional[float]
    content_score: Optional[float]
    fluency_score: Optional[float]
    nonverbal_score: Optional[float]
    speech_metrics: Optional[Any]
    nonverbal_metrics: Optional[Any]
    content_metrics: Optional[Any]
    delta_overall: Optional[float]
    delta_content: Optional[float]
    delta_fluency: Optional[float]
    delta_nonverbal: Optional[float]
    ai_feedback: Optional[List[FeedbackItem]]


@router.get("/{session_id}", response_model=AnalysisOut)
def get_analysis(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    session = db.query(models.Session).filter(
        models.Session.id == session_id,
        models.Session.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = db.query(models.AnalysisResult).filter(
        models.AnalysisResult.session_id == session_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not ready yet")

    feedback_items = [FeedbackItem(**f) for f in (result.ai_feedback or [])]

    return AnalysisOut(
        session_id=session_id,
        overall_score=session.overall_score,
        content_score=session.content_score,
        fluency_score=session.fluency_score,
        nonverbal_score=session.nonverbal_score,
        speech_metrics=result.speech_metrics,
        nonverbal_metrics=result.nonverbal_metrics,
        content_metrics=result.content_metrics,
        delta_overall=result.delta_overall,
        delta_content=result.delta_content,
        delta_fluency=result.delta_fluency,
        delta_nonverbal=result.delta_nonverbal,
        ai_feedback=feedback_items,
    )


@router.get("/history/{user_id}")
def get_score_history(
    db: DBSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Returns score history for the current user (for trend charts)."""
    sessions = (
        db.query(models.Session)
        .filter(
            models.Session.user_id == current_user.id,
            models.Session.completed == True,
            models.Session.overall_score.isnot(None),
        )
        .order_by(models.Session.created_at.asc())
        .all()
    )
    return [
        {
            "session_id": s.id,
            "date": s.created_at.isoformat(),
            "overall_score": s.overall_score,
            "content_score": s.content_score,
            "fluency_score": s.fluency_score,
            "nonverbal_score": s.nonverbal_score,
        }
        for s in sessions
    ]
