"""
services/rag_service.py

RAG service layer — handles all retrieval and context building logic.
Called by RAG Agent to perform semantic search and prepare context.

Usage:
    from backend.app.services.rag_service import search_and_build_context
"""

from openai import OpenAI

from backend.app.config import OPENAI_API_KEY, RAG_TOP_K
from backend.app.database.qdrant_client import search_qdrant


def search_jobs_semantic(
    query: str,
    top_k: int = RAG_TOP_K,
    openai_client: OpenAI = None,
) -> list[dict]:
    """
    Perform semantic search on Qdrant for job documents.

    Args:
        query: user's search query
        top_k: number of results to return

    Returns:
        list of dicts with: score, payload
    """
    results = search_qdrant(
        query=query,
        top_k=top_k,
        openai_client=openai_client,
    )
    return results


def build_context(search_results: list[dict]) -> tuple[str, list[dict]]:
    """
    Build context string from search results for LLM prompt.

    Returns:
        tuple of (context_string, sources_list)
        sources_list: list of dicts with index, job_title, company, score
    """
    if not search_results:
        return "No relevant documents found.", []

    context_parts = []
    sources = []

    for i, result in enumerate(search_results, 1):
        payload = result["payload"]
        score = result["score"]
        doc = payload.get("document", "")
        job_title = payload.get("job_title", "Unknown")
        company = payload.get("company_name", "Unknown")
        location = payload.get("location", "Unknown")

        context_parts.append(
            f"--- Document {i} [Source: {company} - {job_title}] "
            f"(relevance: {score:.2f}) ---\n{doc}"
        )

        sources.append({
            "index": i,
            "job_title": job_title,
            "company_name": company,
            "location": location,
            "relevance_score": round(score, 3),
        })

    return "\n\n".join(context_parts), sources


def format_sources_footer(sources: list[dict]) -> str:
    """
    Format sources into a readable footer for citation.

    Example output:
    ---
    Sumber yang digunakan:
    [1] Infomedia — Officer Data Scientist (Jakarta) | relevance: 0.87
    """
    if not sources:
        return ""

    lines = ["\n---\nSumber yang digunakan:"]
    for s in sources:
        lines.append(
            f"[{s['index']}] {s['company_name']} — {s['job_title']} "
            f"({s['location']}) | relevance: {s['relevance_score']}"
        )

    return "\n".join(lines)


def search_and_build_context(
    query: str,
    top_k: int = RAG_TOP_K,
    openai_client: OpenAI = None,
) -> dict:
    """
    Full RAG service pipeline: search + build context + sources.

    Returns:
        dict with: context, sources, sources_footer, result_count
    """
    results = search_jobs_semantic(query, top_k, openai_client)
    context, sources = build_context(results)
    sources_footer = format_sources_footer(sources)

    return {
        "context": context,
        "sources": sources,
        "sources_footer": sources_footer,
        "result_count": len(results),
    }
