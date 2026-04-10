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
from backend.app.agents.main_agent import classify_intent, handle_chat
from backend.app.services.sql_service import generate_and_execute_query
from backend.app.services.rag_service import search_and_build_context

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
            result = search_and_build_context(message, openai_client=client)
            reply = result.get("context", "No results found")
            source = "RAG Service"

        elif intent in [IntentType.SALARY_INFO, IntentType.LOCATION_STATS]:
            result = generate_and_execute_query(message, openai_client=client)
            reply = result.get("formatted_answer", "No data available")
            source = "SQL Service"

        elif intent in [IntentType.JOB_RECOMMENDATION, IntentType.GREETING]:
            reply = handle_chat(message, client)
            source = "General"

        else:
            reply = handle_chat(message, client)
            source = "General"
        
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
            intent=intent.value if intent else "unknown",
            response=reply,
            source=source,
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