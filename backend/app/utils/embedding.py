"""
utils/embedding.py

Embedding utilities for the Multi-Agent System.
Wraps OpenAI embedding API for reuse across agents and services.
"""

from openai import OpenAI

from backend.app.config import OPENAI_API_KEY, EMBED_MODEL


def get_openai_client(api_key: str = None) -> OpenAI:
    return OpenAI(api_key=api_key or OPENAI_API_KEY)


def get_embedding(text: str, client: OpenAI = None) -> list[float]:
    """
    Embed a single text string.

    Returns a list of floats (vector of size 1536 for text-embedding-3-small).
    """
    if client is None:
        client = get_openai_client()

    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=text,
    )
    return response.data[0].embedding


def get_embeddings(texts: list[str], client: OpenAI = None) -> list[list[float]]:
    """
    Embed a batch of texts in a single API call.

    Returns a list of vectors in the same order as the input texts.
    """
    if client is None:
        client = get_openai_client()

    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]
