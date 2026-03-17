from fastapi import APIRouter, UploadFile, File, Depends, Form
from fastapi.responses import StreamingResponse  # <--- FIX: Added this import
from sqlalchemy.orm import Session
import os, shutil, json

from ..database import get_db
from ..models import ResumeResult
from ..services.resume_parser import parse_resume
from ..services.rag_pipeline import retrieve_relevant_careers
from ..services.ai_engine import extract_skills_with_llm, generate_career_advice, calculate_ats_score, chat_with_bot_stream


router = APIRouter(prefix="/analysis", tags=["Analysis"])
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/{user_id}")
async def analyze_resume(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1. Save & Parse
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    text = parse_resume(file_path, os.path.splitext(file.filename)[1])
    
    # 2. Skills
    skills = extract_skills_with_llm(text)
    
    # 3. ATS
    ats_score, ats_feedback = calculate_ats_score(text, skills)
    
    # 4. RAG Retrieval
    query = ", ".join(skills) if skills else "general career"
    results = retrieve_relevant_careers(query)
    
    docs = []
    # Safe Access
    if results and results.get('documents') and results['documents'][0]:
        docs = results['documents'][0]
    
    # 5. Advice
    advice = generate_career_advice(text, docs, skills)
    
    # 6. Save
    new_result = ResumeResult(
        user_id=user_id,
        filename=file.filename,
        extracted_skills=skills,
        career_recommendations=json.dumps({"advice": advice}),
        roadmap={}
    )
    db.add(new_result)
    db.commit()
    
    return {
        "skills": skills,
        "recommendations": advice,
        "ats_score": ats_score,
        "ats_feedback": ats_feedback,
        "relevant_careers": docs
    }

# ... (keep chat endpoint as is) ...
@router.post("/chat")
def chat(query: str = Form(...), history: str = Form(default="[]")):
    try:
        history_list = json.loads(history)
    except:
        history_list = []
        
    results = retrieve_relevant_careers(query)
    
    # Safe extraction for chat context
    docs = []
    if results and results.get('documents') and len(results['documents']) > 0:
        docs = results['documents'][0]

    return StreamingResponse(
        chat_with_bot_stream(query, docs, history_list), 
        media_type="text/plain"
    )
