"""
core/router.py

Core routing module for the Multi-Agent System.
Single entry point for all API routes to interact with the agent system.

Usage:
    from backend.app.core.router import process_message, process_cv_upload
"""

from backend.app.agents.main_agent import run_agent


def process_message(message: str, chat_history: list = None) -> dict:
    """
    Process a user chat message through the multi-agent system.

    Args:
        message: user's question or request
        chat_history: optional list of previous messages (for context)

    Returns:
        dict with: intent, response, source
    """
    result = run_agent(user_message=message)
    return result


def process_cv_upload(message: str, cv_data: dict) -> dict:
    """
    Process a CV upload + user message through the CV Agent.

    Args:
        message: user's request (e.g. "Rekomendasikan pekerjaan")
        cv_data: parsed CV data from the CV parser
                 Expected format:
                 {
                     "name": "John Doe",
                     "skills": ["python", "sql", "excel"],
                     "experience": "2 years as data analyst at ...",
                     "education": "S1 Informatika ...",
                     "summary": "..."
                 }

    Returns:
        dict with: intent ("cv"), response, source ("CV Agent")
    """
    result = run_agent(user_message=message, cv_data=cv_data)
    return result
