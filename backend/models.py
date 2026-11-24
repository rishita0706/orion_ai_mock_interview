
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    institution = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("Session", back_populates="user")


class Session(Base):
    """One mock interview session = 4 questions answered."""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed = Column(Boolean, default=False)

    # Aggregate scores (filled after processing all answers)
    overall_score = Column(Float, nullable=True)
    content_score = Column(Float, nullable=True)
    fluency_score = Column(Float, nullable=True)
    nonverbal_score = Column(Float, nullable=True)

    user = relationship("User", back_populates="sessions")
    answers = relationship("SessionAnswer", back_populates="session")
    analysis = relationship("AnalysisResult", back_populates="session", uselist=False)


class SessionAnswer(Base):
    """One answer per question within a session."""
    __tablename__ = "session_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    question_id = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    video_path = Column(String, nullable=True)    # stored file path / S3 key
    audio_path = Column(String, nullable=True)
    transcript = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Per-answer scores
    content_score = Column(Float, nullable=True)
    fluency_score = Column(Float, nullable=True)
    nonverbal_score = Column(Float, nullable=True)

    session = relationship("Session", back_populates="answers")


class AnalysisResult(Base):
    """
    Full analysis stored as JSON + scalar scores for one session.
    Includes comparison to previous session.
    """
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Detailed metrics (stored as JSON dict)
    speech_metrics = Column(JSON, nullable=True)
    nonverbal_metrics = Column(JSON, nullable=True)
    content_metrics = Column(JSON, nullable=True)

    # Computed delta vs previous session
    delta_overall = Column(Float, nullable=True)
    delta_content = Column(Float, nullable=True)
    delta_fluency = Column(Float, nullable=True)
    delta_nonverbal = Column(Float, nullable=True)

    # AI-generated text feedback
    ai_feedback = Column(JSON, nullable=True)   # list of {category, text, sentiment}

    session = relationship("Session", back_populates="analysis")
