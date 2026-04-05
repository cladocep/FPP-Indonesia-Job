"""
main.py

FastAPI entry point for the Multi-Agent System.
Provides REST API endpoints for the frontend to connect to.
"""

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import Optional

from backend.app.config import validate_config, APP_PORT
from backend.app.agents.main_agent import run_agent

# ── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Indonesian Job Multi-Agent System",
    description="AI-powered job search with RAG, SQL, and CV agents",
    version="1.0.0",
)


# ── request/response models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    cv_data: Optional[dict] = None


class ChatResponse(BaseModel):
    intent: str
    response: str
    source: str


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
