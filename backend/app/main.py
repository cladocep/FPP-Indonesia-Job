"""
main.py

FastAPI entry point for the Multi-Agent System.
Provides REST API endpoints for the frontend to connect to.
"""

import json as json_lib

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel
from typing import Optional

from backend.app.config import validate_config, APP_PORT, OPENAI_API_KEY, LLM_MODEL
from backend.app.agents.main_agent import run_agent, classify_intent
from backend.app.agents.rag_agent import build_context, format_sources_footer, RAG_SYSTEM_PROMPT
from backend.app.agents.sql_agent import generate_sql, RESULT_FORMATTER_PROMPT
from backend.app.database.qdrant_client import search_qdrant
from backend.app.database.sqlite_db import execute_query
from backend.app.api import routes_chat, routes_cv, routes_recommendation, routes_consultation

# ── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Indonesian Job Multi-Agent System",
    description="AI-powered job search with RAG, SQL, and CV agents",
    version="1.0.0",
)

app.include_router(routes_chat.router)
app.include_router(routes_cv.router)
app.include_router(routes_recommendation.router)
app.include_router(routes_consultation.router)


# ── request/response models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    cv_data: Optional[dict] = None


class ChatResponse(BaseModel):
    intent: str
    response: str
    source: str


# ═══════════════════════════════════════════════════════
# CV ANALYSIS ENDPOINT
# ═══════════════════════════════════════════════════════

@app.post("/api/cv/analyze")
async def analyze_cv(file: UploadFile = File(...)):
    """Analyze CV and return feedback"""
    try:
        content = await file.read()
        # Process CV analysis here
        return {
            "overall_score": 78,
            "strengths": ["Clear structure", "Good experience"],
            "weaknesses": ["Missing keywords", "Poor formatting"],
            "recommendations": ["Add more metrics", "Use action verbs"]
        }
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════
# JOB RECOMMENDATIONS ENDPOINT
# ═══════════════════════════════════════════════════════

class RecommendationRequest(BaseModel):
    current_skills: list[str]
    desired_roles: list[str]
    location: str

@app.post("/api/recommendations/personalized")
async def get_recommendations(req: RecommendationRequest):
    """Get personalized job recommendations"""
    try:
        # Query jobs from database based on skills & location
        return {
            "recommendations": [
                {
                    "job_title": "Backend Developer",
                    "company": "Tech Corp",
                    "location": req.location,
                    "skill_match_percentage": 85
                }
            ]
        }
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════
# CAREER ADVICE ENDPOINT
# ═══════════════════════════════════════════════════════

class CareerAdviceRequest(BaseModel):
    current_role: str
    target_role: str
    current_skills: list[str]
    years_experience: int

@app.post("/api/consultation/career-advice")
async def get_career_advice(req: CareerAdviceRequest):
    """Get personalized career advice"""
    try:
        return {
            "career_advice": f"To grow from {req.current_role} to {req.target_role}, focus on...",
            "timeline": "12-18 months",
            "effort": "High",
            "recommendations": ["Learn new framework", "Build portfolio", "Network"]
        }
    except Exception as e:
        return {"error": str(e)}


# ── endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "running", "service": "Multi-Agent Job Search System"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Main chat endpoint.
    Sends user message to Main Agent → routes to correct agent → returns response.
    """
    result = run_agent(
        user_message=request.message,
        cv_data=request.cv_data,
    )
    return ChatResponse(**result)


@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint using Server-Sent Events.
    Classifies intent, fetches context (blocking), then streams the LLM response token by token.
    """
    def generate():
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        try:
            intent = classify_intent(request.message, openai_client)
            messages = []
            suffix = ""
            source = "Chat"

            if intent == "rag":
                source = "RAG Agent"
                search_results = search_qdrant(request.message, openai_client=openai_client)
                if not search_results:
                    yield f"data: {json_lib.dumps({'type': 'meta', 'intent': intent, 'source': source})}\n\n"
                    yield f"data: {json_lib.dumps({'type': 'token', 'content': 'Maaf, aku tidak menemukan lowongan yang relevan. Coba gunakan kata kunci yang berbeda ya!'})}\n\n"
                    yield f"data: {json_lib.dumps({'type': 'done'})}\n\n"
                    return
                context, sources = build_context(search_results)
                suffix = format_sources_footer(sources)
                system_prompt = RAG_SYSTEM_PROMPT.format(context=context)
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.message},
                ]

            elif intent == "sql":
                source = "SQL Agent"
                try:
                    sql = generate_sql(request.message, openai_client)
                    results = execute_query(sql)
                except Exception:
                    results = []
                results_text = str(results[:50]) if results else "Query returned no results."
                system_prompt = RESULT_FORMATTER_PROMPT.format(
                    question=request.message,
                    results=results_text,
                )
                messages = [{"role": "system", "content": system_prompt}]

            elif intent == "hybrid":
                source = "Hybrid (RAG + SQL)"
                search_results = search_qdrant(request.message, openai_client=openai_client)
                rag_context = ""
                if search_results:
                    rag_context, _ = build_context(search_results)
                try:
                    sql = generate_sql(request.message, openai_client)
                    sql_results = execute_query(sql)
                    sql_context = str(sql_results[:20])
                except Exception:
                    sql_context = "No SQL data available."
                combine_prompt = (
                    f"You are a helpful assistant. Combine these two sources into one clear answer.\n"
                    f"User asked: \"{request.message}\"\n\n"
                    f"Job descriptions (semantic search):\n{rag_context[:1500]}\n\n"
                    f"Database statistics (SQL):\n{sql_context}\n\n"
                    "Rules: Merge naturally. Include both descriptive AND quantitative data. "
                    "Respond in Bahasa Indonesia."
                )
                messages = [{"role": "system", "content": combine_prompt}]

            else:  # chat, cv, unknown
                source = "Chat"
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are a friendly AI assistant for an Indonesian Job Search platform. "
                            "Always respond in Bahasa Indonesia. "
                            "Be helpful and guide users to ask about jobs, salary/statistics, or upload their CV."
                        ),
                    },
                    {"role": "user", "content": request.message},
                ]

            yield f"data: {json_lib.dumps({'type': 'meta', 'intent': intent, 'source': source})}\n\n"

            stream = openai_client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                stream=True,
                temperature=0.3,
                max_tokens=1000,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield f"data: {json_lib.dumps({'type': 'token', 'content': delta.content})}\n\n"

            if suffix:
                yield f"data: {json_lib.dumps({'type': 'token', 'content': suffix})}\n\n"

            yield f"data: {json_lib.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json_lib.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── startup ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup_event():
    """Validate config on startup."""
    try:
        validate_config()
        print("Config validated successfully!")
    except Exception as e:
        print(f"WARNING: Config validation failed: {e}")
        print("Some features may not work without proper configuration.")


# ── run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)
