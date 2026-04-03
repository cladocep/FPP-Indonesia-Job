"""
database/qdrant_client.py

Qdrant vector database connection and search functions.
Used by RAG Agent for semantic search.
"""

from qdrant_client import QdrantClient
from openai import OpenAI

from backend.app.config import (
    QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION,
    OPENAI_API_KEY, EMBED_MODEL, RAG_TOP_K,
)


def get_qdrant_client() -> QdrantClient:
    """Create and return a Qdrant client instance."""
    return QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=60,
    )


def get_openai_client() -> OpenAI:
    """Create and return an OpenAI client instance."""
    return OpenAI(api_key=OPENAI_API_KEY)


def embed_query(query: str, openai_client: OpenAI = None) -> list[float]:
    """Embed a single query text using OpenAI."""
    if openai_client is None:
        openai_client = get_openai_client()

    response = openai_client.embeddings.create(
        model=EMBED_MODEL,
        input=query,
    )
    return response.data[0].embedding


def search_qdrant(
    query: str,
    top_k: int = RAG_TOP_K,
    qdrant: QdrantClient = None,
    openai_client: OpenAI = None,
) -> list[dict]:
    """
    Semantic search on Qdrant.

    Returns list of dicts with keys: score, payload
    """
    if qdrant is None:
        qdrant = get_qdrant_client()
    if openai_client is None:
        openai_client = get_openai_client()

    query_vector = embed_query(query, openai_client)

    results = qdrant.query_points(
    collection_name=QDRANT_COLLECTION,
    query=query_vector,
    limit=top_k,
).points

    return [
        {
            "score": hit.score,
            "payload": hit.payload,
        }
        for hit in results
    ]
