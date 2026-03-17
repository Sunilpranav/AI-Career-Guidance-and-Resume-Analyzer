from sqlalchemy import Column, Integer, String, Boolean, JSON
from .database import Base  

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}  

    # FIX: Removed 'index=True' from id because Primary Keys are auto-indexed.
    # Removed 'index=True' from unique columns to prevent duplicate index errors in MySQL.
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    email = Column(String(100), unique=True)
    hashed_password = Column(String(255))
    
    # New Fields for Email Verification
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(100), nullable=True)


class ResumeResult(Base):
    __tablename__ = "resume_results"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    filename = Column(String(255))
    extracted_skills = Column(JSON)
    career_recommendations = Column(JSON)
    roadmap = Column(JSON)
