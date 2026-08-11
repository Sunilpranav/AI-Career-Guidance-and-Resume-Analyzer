"""
ai_engine.py — All LLM interactions via Groq API.
Model: llama-3.3-70b-versatile (free tier, generous limits, far better than 1B local).
"""

import os
import re
import json
import logging
from typing import Generator

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_client: Groq | None = None
MODEL_NAME = "llama-3.3-70b-versatile"


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Get a free key at https://console.groq.com"
            )
        _client = Groq(api_key=api_key)
    return _client


# ─── ATS Score (pure heuristics, no LLM) ──────────────────────────────────────

IMPORTANT_KEYWORDS = [
    # General professional keywords
    "experience", "skills", "education", "projects", "certifications",
    "achievements", "responsibilities", "summary", "objective",
    # Tech
    "python", "java", "javascript", "typescript", "react", "node", "sql",
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "linux",
    "machine learning", "data science", "api", "rest", "graphql",
    "agile", "scrum", "ci/cd", "devops",
    # Soft skills / action words that ATS likes
    "led", "built", "designed", "implemented", "improved", "managed",
    "developed", "optimized", "collaborated", "delivered",
]


def calculate_ats_score(resume_text: str) -> tuple[int, str]:
    """
    Pure-Python heuristic ATS score: 0–100.
    Returns (score, summary_sentence).
    """
    if not resume_text or not resume_text.strip():
        return 0, "Resume appears to be empty or unreadable."

    text_lower = resume_text.lower()
    word_count = len(resume_text.split())

    # Keyword density
    found = sum(1 for kw in IMPORTANT_KEYWORDS if kw in text_lower)
    keyword_score = min(40, int((found / len(IMPORTANT_KEYWORDS)) * 40))

    # Length score (500–1500 words is ideal)
    if word_count < 200:
        length_score = 10
    elif word_count < 500:
        length_score = 20
    elif word_count <= 1500:
        length_score = 30
    elif word_count <= 2500:
        length_score = 25
    else:
        length_score = 15

    # Section presence
    sections = ["experience", "education", "skills", "projects", "summary", "objective"]
    section_score = min(20, sum(5 for s in sections if s in text_lower))

    # Contact info presence
    has_email = bool(re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', resume_text))
    has_phone = bool(re.search(r'\b[\d\s\-\(\)]{7,15}\b', resume_text))
    contact_score = (5 if has_email else 0) + (5 if has_phone else 0)

    score = keyword_score + length_score + section_score + contact_score
    score = max(0, min(100, score))

    if score >= 80:
        summary = f"Excellent resume structure with strong keyword alignment ({score}/100)."
    elif score >= 60:
        summary = f"Good resume with some gaps in keywords or structure ({score}/100)."
    elif score >= 40:
        summary = f"Resume needs improvement — missing key sections or keywords ({score}/100)."
    else:
        summary = f"Resume requires significant work to pass ATS filters ({score}/100)."

    return score, summary


# ─── Skill Extraction ─────────────────────────────────────────────────────────

def extract_skills_with_llm(resume_text: str) -> list[str]:
    """Extract a categorized skill list from resume text using Groq LLM."""
    client = _get_client()
    prompt = f"""Extract all technical and professional skills from this resume.
Return ONLY a JSON array of skill strings, no markdown, no explanation.
Example: ["Python", "SQL", "React", "Project Management", "Docker"]

Resume:
{resume_text[:4000]}

Return only the JSON array:"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
        )
        raw = response.choices[0].message.content or "[]"

        # Extract JSON array even if model adds surrounding text
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"Skill extraction failed: {e}")
        return []


# ─── Resume Analysis ──────────────────────────────────────────────────────────

def analyze_resume_with_llm(resume_text: str, target_role: str | None = None) -> dict:
    """
    Comprehensive resume analysis returning structured data.
    Returns: {strengths, gaps, suggestions, career_recommendations}
    """
    client = _get_client()

    role_context = f"Target Role: {target_role}" if target_role else "No specific target role — provide general analysis."

    prompt = f"""You are an expert ATS resume analyst and career advisor.
Analyze the resume below and return ONLY a valid JSON object (no markdown, no code fences).

{role_context}

Resume:
---
{resume_text[:6000]}
---

Return this exact JSON structure:
{{
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "gaps": ["<gap or missing keyword 1>", "<gap 2>", "<gap 3>"],
  "suggestions": ["<specific rewrite suggestion 1>", "<suggestion 2>", "<suggestion 3>", "<suggestion 4>"],
  "career_recommendations": ["<career path 1>", "<career path 2>", "<career path 3>"]
}}

Rules:
- strengths: 3-5 specific things the resume does well
- gaps: 3-5 missing keywords, skills, or sections for ATS
- suggestions: 3-5 concrete, actionable rewrite tips
- career_recommendations: 2-4 career paths that match the profile
- Return ONLY the JSON object."""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
        )
        raw = response.choices[0].message.content or "{}"
        json_str = _extract_json_object(raw)
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Resume LLM analysis failed: {e}")
        return {
            "strengths": ["Resume parsed successfully."],
            "gaps": ["Unable to generate detailed analysis at this time."],
            "suggestions": ["Please try again in a moment."],
            "career_recommendations": [],
        }


def generate_career_roadmap(current_role: str, target_role: str) -> dict:
    """Generate a time-boxed career transition roadmap."""
    client = _get_client()

    prompt = f"""You are a career development expert. Create a detailed, time-boxed career transition roadmap.
Return ONLY a valid JSON object (no markdown, no code blocks).

Current Role: {current_role}
Target Role: {target_role}

Return this exact JSON structure:
{{
  "currentRole": "{current_role}",
  "targetRole": "{target_role}",
  "overview": "<2-3 sentence overview of the transition>",
  "stages": [
    {{
      "period": "0–3 months",
      "goal": "<primary goal for this stage>",
      "actions": ["<action 1>", "<action 2>", "<action 3>"],
      "resources": ["<resource 1>", "<resource 2>"]
    }},
    {{
      "period": "3–6 months",
      "goal": "<primary goal>",
      "actions": ["<action 1>", "<action 2>", "<action 3>"],
      "resources": ["<resource 1>", "<resource 2>"]
    }},
    {{
      "period": "6–12 months",
      "goal": "<primary goal>",
      "actions": ["<action 1>", "<action 2>", "<action 3>"],
      "resources": ["<resource 1>", "<resource 2>"]
    }}
  ]
}}

Return ONLY the JSON object."""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1500,
        )
        raw = response.choices[0].message.content or "{}"
        return json.loads(_extract_json_object(raw))
    except Exception as e:
        logger.error(f"Roadmap generation failed: {e}")
        return {
            "currentRole": current_role,
            "targetRole": target_role,
            "overview": "Could not generate roadmap at this time. Please try again.",
            "stages": [],
        }


# ─── Streaming Chat ───────────────────────────────────────────────────────────

CAREER_CHAT_SYSTEM_PROMPT = """You are CareerAI, a warm, professional career advisor with 15+ years of experience across tech, business, and creative industries.

Your personality:
- Friendly and encouraging, never robotic or stiff
- Concise: 2-4 sentences unless detail is genuinely needed
- Specific: give real tool names, frameworks, platforms — not vague advice

Behavior rules:
1. **Greetings & small talk** → respond naturally and warmly. No need to ground these in data.
   Example: User says "hi" → "Hey! I'm here to help with your career journey. What's on your mind?"

2. **Meta questions** (what can you do, how can you help) → explain your capabilities conversationally.
   Example: "I can analyze your resume strengths, suggest career paths, help with interview prep, salary negotiation, and skill gap planning."

3. **Factual career claims** (salary, job requirements, in-demand skills) → ONLY use information from the context provided below or well-established public knowledge. Don't invent salary figures.

4. **Career context** → When the user has uploaded a resume, refer to their specific skills and background when relevant.

Keep the conversation helpful, human, and focused on actionable next steps.

---
{career_context}
"""


def chat_with_bot_stream(
    message: str,
    history: list[dict],
    career_context: str = "",
    retrieved_docs: list[str] | None = None,
) -> Generator[str, None, None]:
    """
    Stream chat responses from Groq.
    Yields text chunks as they arrive.
    """
    client = _get_client()

    # Build context from RAG documents
    docs_context = ""
    if retrieved_docs:
        docs_context = "\n\n".join(
            f"Career Info {i+1}:\n{doc[:900]}" for i, doc in enumerate(retrieved_docs[:5])
        )

    system_content = CAREER_CHAT_SYSTEM_PROMPT.format(
        career_context=career_context or "No resume uploaded yet."
    )
    if docs_context:
        system_content += f"\n\nRelevant career data from knowledge base:\n{docs_context}"

    messages = [{"role": "system", "content": system_content}]

    # Add conversation history (last 10 turns)
    for turn in history[-10:]:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": message})

    try:
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=600,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except RuntimeError as e:
        # Missing API key — yield friendly message
        yield f"⚠️ **Configuration needed:** {e}\n\nTo enable AI chat, set your `GROQ_API_KEY` in the `.env` file. Get a free key at [console.groq.com](https://console.groq.com)."
    except Exception as e:
        logger.error(f"Chat stream error: {e}")
        yield "I'm having trouble connecting right now. Please try again in a moment."


# ─── Utilities ────────────────────────────────────────────────────────────────

def _extract_json_object(raw: str) -> str:
    """Strip markdown fences and find the first {...} JSON object."""
    if not raw:
        return "{}"
    text = raw.strip()
    # Remove markdown code fences
    if text.startswith("```"):
        first_nl = text.find("\n")
        last_fence = text.rfind("```")
        if first_nl > 0 and last_fence > first_nl:
            text = text[first_nl + 1:last_fence].strip()
    # Find outermost {...}
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start:end + 1]
    return text
