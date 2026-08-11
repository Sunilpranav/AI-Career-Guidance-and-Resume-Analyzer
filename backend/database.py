"""
database.py — SQLAlchemy setup with environment-driven connection string.
Reads DATABASE_URL from environment (set in .env locally, Render dashboard in prod).
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()  # no-op in production; reads .env locally

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    # Fallback to SQLite for local dev without a .env file
    DATABASE_URL = "sqlite:///./career_ai.db"
    print("[WARNING] DATABASE_URL not set — using SQLite (local dev only).")

# Neon/Postgres URLs sometimes use 'postgres://' prefix (old style)
# SQLAlchemy >= 1.4 requires 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs connect_args; Postgres does not
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # detect stale connections on free-tier Postgres
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
