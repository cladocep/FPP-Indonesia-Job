"""
test_citation.py
Test RAG Agent with source citation
"""

from backend.app.agents.rag_agent import handle_rag_query

print("=" * 60)
print("RAG AGENT - SOURCE CITATION TEST")
print("=" * 60)

result = handle_rag_query("Cari lowongan yang berhubungan dengan machine learning")
print(result)