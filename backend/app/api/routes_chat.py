"""
api/routes_chat.py

Main chat routing endpoint.
Classifies user intent and routes to appropriate service.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from openai import OpenAI

from backend.app.config import OPENAI_API_KEY
from backend.app.models.response_model import ChatResponse, IntentType
from backend.app.agents.main_agent import classify_intent
from backend.app.services.sql_service import generate_and_execute_query
from backend.app.services.rag_service import search_jobs_rag
from backend.app.services.cv_service import analyze_cv_with_service
from backend.app.services.recommendation_service import get_job_recommendations

router = APIRouter(prefix="/api/chat", tags=["Chat"])
client = OpenAI(api_key=OPENAI_API_KEY)

# Store conversation history
conversation_history = {}


@router.post("/message", response_model=ChatResponse)
async def send_message(
    user_id: str,
    message: str,
    session_id: Optional[str] = None
):
    """
    Send message to main chat endpoint.
    Classifies intent and routes to appropriate service.
    
    Args:
        user_id: User identifier
        message: User message
        session_id: Optional conversation session ID
    
    Returns:
        ChatResponse with agent reply and detected intent
    """
    try:
        # Classify user intent
        intent_str = classify_intent(message, client)
        intent = (
            IntentType(intent_str) 
            if intent_str in IntentType.__members__.values() 
            else IntentType.UNKNOWN
        )
        
        # Route based on intent
        if intent in [IntentType.JOB_SEARCH, IntentType.JOB_DETAILS]:
            # Use RAG service for job search
            result = search_jobs_rag(message, client)
            reply = result.get("formatted_answer", "No results found")
            source = "RAG Service"
            confidence = 0.92
            metadata = {
                "type": "rag",
                "source": "rag_service",
                "results_count": len(result.get("raw_results", []))
            }
        
        elif intent in [IntentType.SALARY_INFO, IntentType.LOCATION_STATS]:
            # Use SQL service for statistics
            result = generate_and_execute_query(message, client)
            reply = result.get("formatted_answer", "No data available")
            source = "SQL Service"
            confidence = 0.90
            metadata = {
                "type": "sql",
                "source": "sql_service",
                "sql_query": result.get("sql", ""),
                "row_count": result.get("row_count", 0)
            }
        
        elif intent == IntentType.JOB_RECOMMENDATION:
            # Use recommendation service
            result = get_job_recommendations(message, client)
            reply = result.get("formatted_answer", "No recommendations available")
            source = "Recommendation Service"
            confidence = 0.88
            metadata = {
                "type": "recommendation",
                "source": "recommendation_service",
                "recommendations_count": len(result.get("recommendations", []))
            }
        
        elif intent == IntentType.GREETING:
            reply = "Halo! Saya adalah AI assistant untuk job search di Indonesia. Ada yang bisa saya bantu? 😊"
            source = "General"
            confidence = 0.99
            metadata = {
                "type": "greeting",
                "source": "general"
            }
        
        else:
            reply = "Maaf, saya tidak bisa memproses request ini. Coba tanya tentang lowongan kerja, gaji, atau rekomendasi karir. 🤔"
            source = "General"
            confidence = 0.3
            metadata = {
                "type": "unknown",
                "source": "general"
            }
        
        # Store in conversation history
        if user_id not in conversation_history:
            conversation_history[user_id] = []
        
        conversation_history[user_id].append({
            "role": "user",
            "content": message,
            "intent": intent.value if intent else None
        })
        conversation_history[user_id].append({
            "role": "assistant",
            "content": reply,
            "source": source
        })
        
        return ChatResponse(
            reply=reply,
            intent=intent,
            source=source,
            confidence=confidence,
            metadata={
                "user_id": user_id,
                "session_id": session_id,
                "history_length": len(conversation_history.get(user_id, [])),
                "service_metadata": metadata
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "success": True,
        "message": "Chat API is healthy",
        "status": "ok"
    }


@router.get("/history/{user_id}")
async def get_conversation_history(user_id: str):
    """Get conversation history for user"""
    try:
        return {
            "user_id": user_id,
            "history": conversation_history.get(user_id, []),
            "total_messages": len(conversation_history.get(user_id, []))
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))