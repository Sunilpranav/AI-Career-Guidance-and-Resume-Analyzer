"""
analysis.py — Resume upload, analysis, career matching, and streaming chat.
"""

import json
import logging
import tempfile
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, ResumeResult
from ..routers.auth import get_current_user
from ..services import resume_parser, ai_engine, rag_pipeline

router = APIRouter(prefix="/analysis", tags=["analysis"])
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class AnalysisResponse(BaseModel):
    id: int
    filename: str
    ats_score: float
    ats_summary: str
    strengths: list[str]
    gaps: list[str]
    suggestions: list[str]
    skills: list[str]
    career_matches: list[dict]


class RoadmapRequest(BaseModel):
    current_role: str
    target_role: str


# ── Upload & Analyze ──────────────────────────────────────────────────────────

@router.post("/upload", response_model=AnalysisResponse)
async def upload_and_analyze(
    file: UploadFile = File(...),
    target_role: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a resume (PDF/DOCX), run full analysis, save to DB, return results.
    """
    # Validate extension
    filename = file.filename or "resume"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{ext}'. Only PDF and DOCX are accepted.",
        )

    # Read into temp file (secure, no path traversal)
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 10 MB limit.",
        )

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        # Extract text
        try:
            resume_text = resume_parser.extract_text(tmp_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not read resume: {str(e)}",
            )

        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Resume appears to be empty or contains only images. Please upload a text-based PDF or DOCX.",
            )

        # ATS score (heuristic — fast, no LLM cost)
        ats_score, ats_summary = ai_engine.calculate_ats_score(resume_text)

        # Skill extraction + LLM analysis (parallel via Groq)
        skills = ai_engine.extract_skills_with_llm(resume_text)
        llm_analysis = ai_engine.analyze_resume_with_llm(resume_text, target_role)

        # Career matching from RAG data
        career_matches = rag_pipeline.find_matching_careers(skills, top_n=6)
        career_match_summaries = [
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "match_percentage": c.get("match_percentage", 0),
                "matched_skills": c.get("matched_skills", [])[:5],
                "missing_skills": c.get("missing_skills", [])[:5],
                "salary_range": c.get("salary_range", ""),
            }
            for c in career_matches
        ]

        # Save to database
        result = ResumeResult(
            user_id=current_user.id,
            filename=filename,
            ats_score=ats_score,
            ats_summary=ats_summary,
            strengths=json.dumps(llm_analysis.get("strengths", [])),
            gaps=json.dumps(llm_analysis.get("gaps", [])),
            suggestions=json.dumps(llm_analysis.get("suggestions", [])),
            skills=json.dumps(skills),
            career_matches=json.dumps([c["title"] for c in career_match_summaries]),
        )
        db.add(result)
        db.commit()
        db.refresh(result)

        return AnalysisResponse(
            id=result.id,
            filename=result.filename,
            ats_score=ats_score,
            ats_summary=ats_summary,
            strengths=llm_analysis.get("strengths", []),
            gaps=llm_analysis.get("gaps", []),
            suggestions=llm_analysis.get("suggestions", []),
            skills=skills,
            career_matches=career_match_summaries,
        )

    finally:
        # Always clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ── Career Details ────────────────────────────────────────────────────────────

@router.get("/careers")
def get_all_careers(current_user: User = Depends(get_current_user)):
    """Return all available career paths."""
    return rag_pipeline.get_all_careers()


@router.get("/careers/{career_id}")
def get_career_detail(career_id: str, current_user: User = Depends(get_current_user)):
    """Return detailed info for a specific career."""
    career = rag_pipeline.get_career_by_id(career_id)
    if not career:
        raise HTTPException(status_code=404, detail="Career not found.")
    return career


# ── Career Roadmap ────────────────────────────────────────────────────────────

@router.post("/roadmap")
def generate_roadmap(
    body: RoadmapRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate a personalized career transition roadmap."""
    if not body.current_role.strip() or not body.target_role.strip():
        raise HTTPException(
            status_code=422,
            detail="Both current_role and target_role are required.",
        )
    return ai_engine.generate_career_roadmap(body.current_role, body.target_role)


# ── Streaming Chat ────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Stream career advice from Groq LLM with RAG context.
    Returns text/event-stream (SSE).
    """
    if not body.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    # Get RAG docs for context
    retrieved_docs = rag_pipeline.retrieve_relevant_careers(body.message, n_results=5)

    # Build career context from user's latest resume result
    career_context = ""
    latest_result = (
        db.query(ResumeResult)
        .filter(ResumeResult.user_id == current_user.id)
        .order_by(ResumeResult.created_at.desc())
        .first()
    )
    if latest_result:
        skills = json.loads(latest_result.skills or "[]")
        careers = json.loads(latest_result.career_matches or "[]")
        career_context = (
            f"User's extracted skills: {', '.join(skills[:15])}\n"
            f"Top career matches: {', '.join(careers[:3])}\n"
            f"ATS score: {latest_result.ats_score}/100"
        )

    history = [{"role": m.role, "content": m.content} for m in body.history]

    def event_stream():
        for chunk in ai_engine.chat_with_bot_stream(
            message=body.message,
            history=history,
            career_context=career_context,
            retrieved_docs=retrieved_docs,
        ):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── History ───────────────────────────────────────────────────────────────────

@router.get("/history")
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all resume analysis history for the current user."""
    results = (
        db.query(ResumeResult)
        .filter(ResumeResult.user_id == current_user.id)
        .order_by(ResumeResult.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "ats_score": r.ats_score,
            "ats_summary": r.ats_summary,
            "career_matches": json.loads(r.career_matches or "[]"),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in results
    ]


@router.get("/history/{result_id}")
def get_history_detail(
    result_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return full details of a specific resume analysis result."""
    result = (
        db.query(ResumeResult)
        .filter(
            ResumeResult.id == result_id,
            ResumeResult.user_id == current_user.id,
        )
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found.")

    return {
        "id": result.id,
        "filename": result.filename,
        "ats_score": result.ats_score,
        "ats_summary": result.ats_summary,
        "strengths": json.loads(result.strengths or "[]"),
        "gaps": json.loads(result.gaps or "[]"),
        "suggestions": json.loads(result.suggestions or "[]"),
        "skills": json.loads(result.skills or "[]"),
        "career_matches": json.loads(result.career_matches or "[]"),
        "created_at": result.created_at.isoformat() if result.created_at else None,
    }


@router.delete("/history/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history(
    result_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a specific resume analysis result."""
    result = (
        db.query(ResumeResult)
        .filter(
            ResumeResult.id == result_id,
            ResumeResult.user_id == current_user.id,
        )
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found.")
    db.delete(result)
    db.commit()
