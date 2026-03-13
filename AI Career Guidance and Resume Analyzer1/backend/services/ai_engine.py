import ollama
import json

MODEL_NAME = "llama3.2:1b-instruct-q4_K_M"

def extract_skills_with_llm(resume_text):
    prompt = f"""
    Analyze the following resume text. Extract a JSON list of technical skills and soft skills.
    IMPORTANT: Output ONLY the JSON list. No other text, no introduction, no explanation.
    
    Resume Text:
    {resume_text[:2000]}
    
    JSON Output:
    """
    try:
        response = ollama.chat(model=MODEL_NAME, messages=[
            {'role': 'user', 'content': prompt}
        ])
        content = response['message']['content']
        
        # Improved Cleanup Logic
        # 1. Find the first '['
        start = content.find('[')
        # 2. Find the last ']'
        end = content.rfind(']') + 1
        
        if start != -1 and end > start:
            json_str = content[start:end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                print(f"Could not parse extracted JSON: {json_str}")
                return []
        else:
            print("No JSON list found in AI response.")
            return []
            
    except Exception as e:
        print(f"Error extracting skills: {e}")
        return []

def generate_career_advice(resume_text, retrieved_careers, skills):
    context = "\n".join([str(c) for c in retrieved_careers])
    
    prompt = f"""
    You are a Career Advisor AI.
    
    User Skills: {skills}
    
    Relevant Career Information from Database:
    {context}
    
    Based on the user's skills and the retrieved career information:
    1. Recommend the top career path.
    2. Explain why it fits.
    3. Identify missing skills for this career.
    4. Provide a short learning roadmap.
    
    Format the output clearly.
    """

    response = ollama.chat(model=MODEL_NAME, messages=[
        {'role': 'user', 'content': prompt}
    ])
    return response['message']['content']

def chat_with_bot(user_query, context_docs):
    context = "\n".join([str(c) for c in context_docs])
    prompt = f"""
    You are an AI Career Counselor. Use the following context to answer the user's question.
    Context: {context}
    User Question: {user_query}
    Answer:
    """
    response = ollama.chat(model=MODEL_NAME, messages=[
        {'role': 'user', 'content': prompt}
    ])
    return response['message']['content']