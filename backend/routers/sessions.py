
import os
import uuid
import random
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from routers.auth import get_current_user
import models
from services.pipeline import run_analysis_pipeline

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

QUESTION_BANK = [
    {"id": 1,  "domain": "Interview",    "text": "Tell me about a time you faced a challenge and how you resolved it."},
    {"id": 2,  "domain": "Interview",    "text": "Why did you choose your field of study?"},
    {"id": 3,  "domain": "Interview",    "text": "Describe a project you are proud of and explain your role in it."},
    {"id": 4,  "domain": "Interview",    "text": "How do you handle working under pressure or tight deadlines?"},
    {"id": 5,  "domain": "Viva",         "text": "Summarise the main contribution of your project or research in simple terms."},
    {"id": 6,  "domain": "Viva",         "text": "What are the limitations of your work and how would you address them?"},
    {"id": 7,  "domain": "Viva",         "text": "Explain your methodology to someone unfamiliar with your field."},
    {"id": 8,  "domain": "Communication","text": "Describe how your city or hometown has changed in the last ten years."},
    {"id": 9,  "domain": "Communication","text": "Explain a concept from your field to a complete non-expert."},
    {"id": 10, "domain": "Communication","text": "What skill do you think is most important for professional success, and why?"},
]


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class QuestionOut(BaseModel):
    id: int
    domain: str
    text: str

class SessionCreateResponse(BaseModel):
    session_id: int
    questions: List[QuestionOut]

class AnswerResponse(BaseModel):
    answer_id: int
    message: str

class SessionSummary(BaseModel):
    id: int
    created_at: datetime
    completed: bool
    overall_score: Optional[float]
    content_score: Optional[float]
    fluency_score: Optional[float]
    nonverbal_score: Optional[float]

    class Config:
        from_attributes = True

class AnswerDetail(BaseModel):
    id: int
    question_id: int
    question_text: str
    transcript: Optional[str]
    duration_seconds: Optional[float]
    content_score: Optional[float]
    fluency_score: Optional[float]
    nonverbal_score: Optional[float]

    class Config:
        from_attributes = True

class SessionDetail(BaseModel):
    id: int
    created_at: datetime
    completed: bool
    overall_score: Optional[float]
    content_score: Optional[float]
    fluency_score: Optional[float]
    nonverbal_score: Optional[float]
    answers: List[AnswerDetail]

    class Config:
        from_attributes = True


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/", response_model=SessionCreateResponse, status_code=201)
def create_session(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Creates a new session and assigns 4 random questions."""
    session = models.Session(user_id=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)

    selected = random.sample(QUESTION_BANK, 4)
    return {"session_id": session.id, "questions": selected}


@router.post("/{session_id}/answers", response_model=AnswerResponse)
async def upload_answer(
    session_id: int,
    question_id: int = Form(...),
    question_text: str = Form(...),
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Receives a video blob for one answer and saves it to disk."""
    session = db.query(models.Session).filter(
        models.Session.id == session_id,
        models.Session.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save uploaded file
    ext = os.path.splitext(video.filename)[-1] or ".webm"
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        content = await video.read()
        f.write(content)

    answer = models.SessionAnswer(
        session_id=session_id,
        question_id=question_id,
        question_text=question_text,
        video_path=file_path,
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)

    return {"answer_id": answer.id, "message": "Answer saved"}


@router.post("/{session_id}/complete")
def complete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Marks session as complete and triggers the full analysis pipeline.
    In production this should be async / background task.
    """
    session = db.query(models.Session).filter(
        models.Session.id == session_id,
        models.Session.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.completed = True
    db.commit()

    # Run analysis pipeline (synchronous here, use BackgroundTasks in production)
    try:
        run_analysis_pipeline(session_id=session_id, user_id=current_user.id, db=db)
    except Exception as e:
        print(f"[ORION] Pipeline error for session {session_id}: {e}")

    db.refresh(session)
    return {
        "message": "Analysis complete",
        "session_id": session_id,
        "overall_score": session.overall_score,
    }


@router.get("/", response_model=List[SessionSummary])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Session)
        .filter(models.Session.user_id == current_user.id)
        .order_by(models.Session.created_at.desc())
        .all()
    )


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    session = db.query(models.Session).filter(
        models.Session.id == session_id,
        models.Session.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
