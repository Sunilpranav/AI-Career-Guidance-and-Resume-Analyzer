from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import os, shutil, json

from ..database import get_db
from ..models import ResumeResult
from ..services.resume_parser import parse_resume
from ..services.rag_pipeline import retrieve_relevant_careers
# FIXED IMPORTS: Use the stream function
from ..services.ai_engine import extract_skills_with_llm, generate_career_advice, chat_with_bot_stream

router = APIRouter(prefix="/analysis", tags=["Analysis"])
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/{user_id}")
async def analyze_resume(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    ext = os.path.splitext(file.filename)[1]
    text = parse_resume(file_path, ext)
    
    skills = extract_skills_with_llm(text)
    query = ", ".join(skills)
    results = retrieve_relevant_careers(query)
    advice = generate_career_advice(text, results['documents'], skills)
    
    res = ResumeResult(user_id=user_id, filename=file.filename, extracted_skills=skills, career_recommendations={"advice": advice}, roadmap={})
    db.add(res)
    db.commit()
    
    return {"skills": skills, "recommendations": advice, "relevant_careers": results['documents']}

@router.post("/chat")
def chat(query: str = Form(...), history: str = Form(default="[]")): # Accept history as JSON string
    import json
    # Parse history from string to list
    try:
        history_list = json.loads(history)
    except:
        history_list = []
        
    # Retrieve context
    results = retrieve_relevant_careers(query)
    
    # Return Streaming Response
    return StreamingResponse(
        chat_with_bot_stream(query, results['documents'], history_list), 
        media_type="text/plain"
    )
