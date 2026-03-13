from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from sqlalchemy.orm import Session
import os, shutil, json

from ..database import get_db
from ..models import ResumeResult
from ..services.resume_parser import parse_resume
from ..services.rag_pipeline import retrieve_relevant_careers
from ..services.ai_engine import extract_skills_with_llm, generate_career_advice, chat_with_bot

router = APIRouter(prefix="/analysis", tags=["Analysis"])
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/{user_id}")
async def analyze_resume(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    ext = os.path.splitext(file.filename)[1]
    resume_text = parse_resume(file_path, ext)
    
    skills = extract_skills_with_llm(resume_text)
    query = ", ".join(skills)
    relevant_careers = retrieve_relevant_careers(query)
    advice = generate_career_advice(resume_text, relevant_careers['documents'], skills)
    
    new_result = ResumeResult(
        user_id=user_id,
        filename=file.filename,
        extracted_skills=skills,
        career_recommendations={"advice": advice},
        roadmap={}
    )
    db.add(new_result)
    db.commit()
    
    return {
        "skills": skills,
        "recommendations": advice,
        "relevant_careers": relevant_careers['documents']
    }

@router.post("/chat")
def career_chat(query: str = Form(...)):
    context = retrieve_relevant_careers(query)
    response = chat_with_bot(query, context['documents'])
    return {"response": response}