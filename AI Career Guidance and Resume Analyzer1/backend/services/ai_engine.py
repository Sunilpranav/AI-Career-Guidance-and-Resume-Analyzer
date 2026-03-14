import ollama
import json
import re

MODEL_NAME = "llama3.2:1b-instruct-q4_K_M"

def extract_skills_with_llm(resume_text):
    prompt = f"""
    Analyze the following resume text. Extract a JSON list of technical skills.
    Only output the JSON list. No other text.
    
    Resume Text:
    {resume_text[:2000]}
    """
    try:
        response = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
        content = response['message']['content']
        
        # Robust parsing: find the first [ and last ]
        start = content.find('[')
        end = content.rfind(']') + 1
        
        if start != -1 and end > start:
            json_str = content[start:end]
            try:
                return json.loads(json_str)
            except:
                return []
        return []
    except Exception as e:
        print(f"Error extracting skills: {e}")
        return []

def generate_career_advice(resume_text, retrieved_careers, skills):
    context = "\n".join([str(c) for c in retrieved_careers])
    
    prompt = f"""
    You are an expert Career Advisor. Analyze the user's skills and provide a structured career report.
    
    User Skills: {skills}
    Context from Database: {context}

    Output ONLY valid Markdown.

    ## 🎯 Top Career Match
    [Job Title]

    ## 💡 Why It Fits
    [Explanation]

    ## 📈 Missing Skills to Acquire
    * Skill 1
    * Skill 2

    ## 🗺️ Learning Roadmap
    1. **Step 1:** [Action]
    2. **Step 2:** [Action]
    3. **Step 3:** [Action]
    
    ## 💰 Salary Expectations
    [Range]
    """
    
    response = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
    return response['message']['content']

def chat_with_bot_stream(user_query, context_docs, history=[]):
    # 1. Prepare Context (The Knowledge Base)
    # We join the retrieved documents. If empty, we note that.
    context_str = "\n\n---\n\n".join([str(doc) for doc in context_docs if doc])
    
    # 2. Define the System Persona (The Brain)
    system_prompt = f"""
    You are **CareerAI**, a world-class Career Mentor inspired by ChatGPT.
    
    ### INTELLECT & BEHAVIOR:
    - **Conversational**: Speak naturally, like a helpful human mentor. Avoid robotic phrasing.
    - **Context-Aware**: Use the 'CAREER_DATABASE' below to answer factual questions about jobs, skills, and salaries.
    - **Memory-Aware**: Use 'CHAT_HISTORY' to remember personal details (like the user's name).
    - **Intelligent**: If the user asks a question unrelated to careers (e.g., "What is Java?"), answer it helpfully using general knowledge, then guide back to careers.
    - **Concise**: Keep answers short and punchy unless asked for details.
    - **Proactive**: Always end with a relevant, engaging question to keep the conversation moving.

    ### STRICT GROUNDING RULES:
    - **DO NOT** assume the user's job title or salary from the 'CAREER_DATABASE'. The database contains general data, not the user's personal data.
    - If you don't know the answer based on the database or history, say so honestly.
    - **NEVER** mention "Context", "Data", "System", or "Database" to the user. Just answer naturally.

    ### CURRENT CAREER DATABASE:
    {context_str if context_str else "No specific career data retrieved for this query. Use general knowledge."}
    """

    # 3. Build Messages List
    messages = [{'role': 'system', 'content': system_prompt}]

    # 4. Add Chat History (Memory)
    # We inject the history which contains the user's name and past questions
    # We limit to last 10 messages to prevent token overflow
    limited_history = history[-10:]
    for msg in limited_history:
        if msg.get('role') in ['user', 'assistant'] and msg.get('content'):
            messages.append({'role': msg['role'], 'content': msg['content']})

    # 5. Add Current User Query
    messages.append({'role': 'user', 'content': user_query})

    # 6. Stream Response
    try:
        stream = ollama.chat(model=MODEL_NAME, messages=messages, stream=True)
        for chunk in stream:
            if 'content' in chunk['message']:
                yield chunk['message']['content']
    except Exception as e:
        yield f"[Error connecting to AI: {e}]"
