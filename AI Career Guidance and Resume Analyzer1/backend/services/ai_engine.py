import ollama
import json
import re
import ast

MODEL_NAME = "llama3.2:1b-instruct-q4_K_M"

# --- 1. ADVANCED ATS CALCULATOR ---


# --- 1. ADVANCED ATS CALCULATOR (FRESHER vs PROFESSIONAL) ---
def calculate_ats_score(resume_text, skills):
    score = 0
    feedback = []
    text_lower = resume_text.lower()
    
    # --- STEP 1: DETECT PROFILE TYPE ---
    # Heuristic: Check for Experience section or date ranges
    exp_keywords = ["experience", "work history", "employment", "professional background"]
    has_experience_section = any(k in text_lower for k in exp_keywords)
    
    # Check for graduation years (2022, 2023, 2024 -> likely Fresher)
    import re
    years = re.findall(r'\b(20\d{2})\b', resume_text)
    current_year = 2024 # Static for simplicity, or use datetime
    
    is_fresher = False
    if not has_experience_section:
        is_fresher = True
    
    # If they have explicit fresher keywords
    if any(k in text_lower for k in ["fresher", "student", "intern", "academic project"]):
        is_fresher = True

    # --- STEP 2: CALCULATE SCORE BASED ON TYPE ---
    
    # A. KEYWORD & SKILL MATCH (40 Marks)
    num_skills = len(skills)
    if num_skills >= 10: score += 40
    elif num_skills >= 6: score += 30
    elif num_skills >= 3: score += 20
    else: score += 10; feedback.append("Add more technical keywords relevant to the job.")

    if is_fresher:
        # --- FRESHER FORMULA ---
        
        # B. Projects Relevance (25 Marks)
        if "project" in text_lower or "github" in text_lower:
            score += 20
            if "github" in text_lower: score += 5 # Bonus for links
        else:
            feedback.append("Add a 'Projects' section detailing your academic/personal work.")

        # C. Education (15 Marks)
        if "education" in text_lower or "degree" in text_lower or "gpa" in text_lower:
            score += 12
        else:
            feedback.append("Add 'Education' section with CGPA/Degree.")

        # D. Certifications (10 Marks)
        if "certification" in text_lower or "course" in text_lower or "udemy" in text_lower or "coursera" in text_lower:
            score += 8
        else:
            feedback.append("Add relevant Certifications to stand out.")

    else:
        # --- PROFESSIONAL FORMULA ---

        # B. Work Experience (30 Marks)
        if has_experience_section:
            score += 25
            # Bonus for achievements
            if any(k in text_lower for k in ["achieved", "improved", "managed", "developed"]):
                score += 5
        else:
            feedback.append("Add 'Work Experience' with measurable achievements.")

        # C. Projects / Achievements (10 Marks)
        if "project" in text_lower or "achievement" in text_lower:
            score += 8
        else:
            feedback.append("Highlight key Projects or Achievements.")

        # D. Education (10 Marks)
        if "education" in text_lower:
            score += 8
        else:
            feedback.append("Include your Education background.")

    # E. Resume Format (5 Marks)
    headers = ["skills", "education", "experience", "projects", "summary"]
    found_h = sum(1 for h in headers if h in text_lower)
    if found_h >= 4: score += 5
    elif found_h >= 2: score += 3
    else: feedback.append("Use standard section headers (Skills, Experience, etc).")

    # F. Grammar & Contact (5 Marks)
    if "@" in resume_text and "linkedin" in text_lower:
        score += 5
    elif "@" in resume_text:
        score += 3
    else:
        feedback.append("Add Email and LinkedIn profile.")

    # Cap Score
    final_score = min(score, 95)
    
    if not feedback: feedback.append("Excellent optimization!")
    
    return final_score, feedback
# ... (Keep calculate_ats_score the same) ...

# --- 2. ROBUST SKILL EXTRACTOR (FIXES CRASH) ---
def extract_skills_with_llm(resume_text):
    prompt = f"""
    Extract a JSON list of technical skills from this text.
    RULES:
    - Include ONLY: Programming Languages, Tools, Frameworks.
    - EXCLUDE: Names, Schools, Soft Skills.
    Resume: {resume_text[:1500]}
    Output ONLY the JSON list.
    """
    skills = []
    
    try:
        response = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
        content = response['message']['content']
        
        # FIX: Use Regex to find strictly the FIRST list [...]
        # This ignores extra text or second lists after the first one
        match = re.search(r'\[[\s\S]*?\]', content)
        
        if match:
            list_str = match.group(0)
            
            # Try JSON
            try:
                skills = json.loads(list_str)
            except:
                # Try Python Literal (handles single quotes)
                try:
                    skills = ast.literal_eval(list_str)
                except Exception as e:
                    print(f"Parse Error: {e}")

        # Clean list
        clean_skills = []
        stop_words = ["school", "college", "sslc", "hsc", "unju", "sunil", "pranav"]
        for item in skills:
            if isinstance(item, str):
                item_lower = item.lower()
                if len(item) < 3 or len(item) > 30: continue
                if any(stop in item_lower for stop in stop_words): continue
                clean_skills.append(item)
                
        if clean_skills: return clean_skills

    except Exception as e:
        print(f"LLM Skill Extraction Failed: {e}")

    # FALLBACK: Keyword Search
    print("Falling back to Keyword Search...")
    common_keywords = [
        "python", "java", "javascript", "sql", "html", "css", "react", "angular", "vue",
        "node", "express", "django", "flask", "spring", "git", "github", "docker",
        "aws", "azure", "linux", "c++", "c#", "php", "ruby", "swift", "kotlin",
        "machine learning", "data science", "pandas", "numpy"
    ]
    
    text_lower = resume_text.lower()
    found = []
    for kw in common_keywords:
        if kw in text_lower:
            found.append(kw.title())
            
    return found


# --- 2. STRICT CAREER MATCHING ---
def generate_career_advice(resume_text, retrieved_careers, skills):
    skills_str = ", ".join(skills)
    
    # ONE-SHOT PROMPT: Shows the AI exactly what to do
    prompt = f"""
    You are a career advisor.
    Skills: {skills_str}
    
    Output a career match and a roadmap.
    CRITICAL FORMATTING RULES:
    1. Do NOT use Markdown headers (no ###, ##, or #).
    2. Do NOT use Bold (no **).
    3. Use plain text only.
    
    USE EXACT FORMAT:
    ## 🎯 Top Career Match
    [Job Title]

    ## 💡 Why It Fits
    [Reason]

    ## 📈 Missing Skills
    * [Skill]

    ## 🗺️ Learning Roadmap
    Step 1: [Action]
    Step 2: [Action]
    Step 3: [Action]
    Step 4: [Action]
    Step 5: [Action]

    ## 💰 Salary
    [Range]
    """
    
    response = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
    return response['message']['content']

# --- 4. CHAT STREAM ---
def chat_with_bot_stream(user_query, context_docs, history=[], user_profile=""):
    # 1. PREPARE CONTEXT
    # Limit context to prevent overwhelming the small model
    context_str = "\n\n".join([str(doc)[:500] for doc in context_docs if doc][:3]) 
    
    system_prompt = f"""
    You are 'CareerAI', a precise and accurate Career Mentor.

    ### CRITICAL INSTRUCTION: GROUNDING
    You MUST base your answers on the "PROVIDED DATA" below.
    - If the answer is in the PROVIDED DATA, use it.
    - If the answer is NOT in the PROVIDED DATA, say "I don't have that specific information."
    - DO NOT use your own memory or training data if it conflicts with PROVIDED DATA.

    ### PROVIDED DATA:
    1. USER PROFILE:
    {user_profile}

    2. CAREER KNOWLEDGE BASE:
    {context_str}

    ### STYLE:
    - Be concise (2-3 sentences).
    - Be accurate.
    - You are an AI.
    """

    messages = [{'role': 'system', 'content': system_prompt}]
    
    # Add chat history
    for msg in history[-6:]: messages.append(msg)
    
    # Add current query
    messages.append({'role': 'user', 'content': user_query})

    # Stream response
    stream = ollama.chat(model=MODEL_NAME, messages=messages, stream=True)
    for chunk in stream:
        if 'content' in chunk['message']:
            yield chunk['message']['content']
