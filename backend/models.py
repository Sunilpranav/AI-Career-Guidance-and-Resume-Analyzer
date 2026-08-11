"""
models.py — SQLAlchemy ORM models (User + ResumeResult).
Tables are created on startup via Base.metadata.create_all().
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # One user → many resume results
    resume_results = relationship("ResumeResult", back_populates="owner", cascade="all, delete-orphan")


class ResumeResult(Base):
    __tablename__ = "resume_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    ats_score = Column(Float, default=0)
    ats_summary = Column(Text, default="")
    strengths = Column(Text, default="[]")       # JSON-encoded list
    gaps = Column(Text, default="[]")             # JSON-encoded list
    suggestions = Column(Text, default="[]")      # JSON-encoded list
    skills = Column(Text, default="[]")           # extracted skills JSON
    career_matches = Column(Text, default="[]")   # career recommendation titles JSON
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="resume_results")
