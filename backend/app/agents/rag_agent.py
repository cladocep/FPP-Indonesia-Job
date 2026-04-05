"""
agents/rag_agent.py

RAG Agent (Retrieval-Augmented Generation)

Flow:
1. Embed user query
2. Search Qdrant for relevant job documents
3. Build context from retrieved docs
4. LLM generates answer based on context WITH source citations

Handles questions like:
- "Ceritakan tentang lowongan data scientist di Tokopedia"
- "Apa saja skill yang dibutuhkan untuk backend engineer?"
- "Cari lowongan yang berhubungan dengan machine learning"
"""

from openai import OpenAI

from backend.app.config import OPENAI_API_KEY, LLM_MODEL, RAG_TOP_K
from backend.app.database.qdrant_client import search_qdrant


# ── prompts ──────────────────────────────────────────────────────────────────

RAG_SYSTEM_PROMPT = """You are a helpful Indonesian Job Search assistant.
You answer questions based on the job listing documents provided below.

Rules:
1. ONLY use information from the provided documents to answer.
2. If the documents don't contain relevant info, say so honestly.
3. Respond in the same language the user uses (Indonesian or English).
4. Format your answer clearly — mention job title, company, location when relevant.
5. If multiple jobs match, summarize the key ones (max 5).
6. ALWAYS cite your sources using the format [Source: Company - Job Title] after each piece of information.
7. At the end of your answer, add a "Sumber:" section listing all documents used.
8. If no exact match is found, suggest similar or related roles from the documents available.
   For example, if user asks about "frontend developer" but only "fullstack" or "software engineer" exists, mention those as alternatives.

Documents:
{context}
"""


# ── context builder ──────────────────────────────────────────────────────────

def build_context(search_results: list[dict]) -> tuple[str, list[dict]]:
    """
    Build context string from Qdrant search results.

    Returns:
        tuple of (context_string, sources_list)
        sources_list contains dicts with: index, job_title, company, score
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
    Format sources into a readable footer.

    Example:
    ---
    Sumber:
    [1] Infomedia — Officer Data Scientist (Jakarta Raya) | relevance: 0.87
    [2] Datapower — ML Consultant (Jakarta Barat) | relevance: 0.82
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


# ── main handler ─────────────────────────────────────────────────────────────

def handle_rag_query(
    user_message: str,
    openai_client: OpenAI = None,
    top_k: int = RAG_TOP_K,
) -> str:
    """
    Handle a RAG query end-to-end with source citations.

    1. Search Qdrant
    2. Build context with source labels
    3. Generate answer with LLM (includes inline citations)
    4. Append sources footer
    """
    if openai_client is None:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)

    # Step 1: Semantic search
    print(f"[RAG Agent] Searching Qdrant for: {user_message[:60]}...")
    search_results = search_qdrant(
        query=user_message,
        top_k=top_k,
        openai_client=openai_client,
    )

    if not search_results:
        return (
            "Maaf, aku tidak menemukan lowongan yang relevan dengan pertanyaan kamu. "
            "Coba gunakan kata kunci yang berbeda ya!"
        )

    # Step 2: Build context with source labels
    context, sources = build_context(search_results)

    # Step 3: Generate answer with citations
    print(f"[RAG Agent] Found {len(search_results)} documents, generating answer...")
    system_prompt = RAG_SYSTEM_PROMPT.format(context=context)

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=1000,
    )

    answer = response.choices[0].message.content

    # Step 4: Append sources footer
    sources_footer = format_sources_footer(sources)
    full_response = answer + sources_footer

    return full_response
