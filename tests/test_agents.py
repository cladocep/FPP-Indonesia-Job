"""
test_agents.py

Comprehensive test for all agents in the multi-agent system.
Tests: Main Agent routing, RAG Agent, SQL Agent, CV Agent, Hybrid
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.agents.main_agent import run_agent, classify_intent
from backend.app.agents.rag_agent import handle_rag_query
from backend.app.agents.sql_agent import handle_sql_query
from backend.app.agents.cv_agent import handle_cv_query
from backend.app.config import OPENAI_API_KEY
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

passed = 0
failed = 0


def test(name, func):
    global passed, failed
    print(f"\n{'=' * 60}")
    print(f"TEST: {name}")
    print(f"{'=' * 60}")
    try:
        func()
        passed += 1
        print(f"RESULT: PASSED ✅")
    except Exception as e:
        failed += 1
        print(f"RESULT: FAILED ❌ — {e}")


# ── Test 1: Main Agent Routing ───────────────────────────────────────────

def test_routing():
    cases = [
        ("Berapa jumlah lowongan di Jakarta?", "sql"),
        ("Ceritakan tentang lowongan data scientist", "rag"),
        ("Rekomendasikan pekerjaan berdasarkan CV saya", "cv"),
        ("Halo, apa kabar?", "chat"),
    ]

    for msg, expected in cases:
        intent = classify_intent(msg, client)
        status = "✅" if intent == expected else "❌"
        print(f"  {status} '{msg[:45]}...' → {intent} (expected: {expected})")
        assert intent == expected, f"Expected {expected}, got {intent}"


# ── Test 2: SQL Agent ────────────────────────────────────────────────────

def test_sql_agent():
    result = handle_sql_query("Berapa jumlah total lowongan di database?", client)
    print(f"  Response: {result[:150]}...")
    assert len(result) > 0, "SQL Agent returned empty response"
    assert "473" in result or "lowongan" in result.lower(), "Response should mention job count"


# ── Test 3: RAG Agent ────────────────────────────────────────────────────

def test_rag_agent():
    result = handle_rag_query("Cari lowongan data scientist", client)
    print(f"  Response: {result[:150]}...")
    assert len(result) > 0, "RAG Agent returned empty response"
    assert "Sumber" in result, "Response should contain source citations"


# ── Test 4: CV Agent ─────────────────────────────────────────────────────

def test_cv_agent():
    fake_cv = {
        "name": "Test User",
        "skills": ["python", "sql", "excel", "data analysis", "machine learning"],
        "experience": "2 tahun sebagai data analyst di startup fintech",
        "education": "S1 Sistem Informasi",
        "summary": "Data analyst yang ingin transisi ke data scientist",
    }

    result = handle_cv_query(
        user_message="Rekomendasikan pekerjaan yang cocok untuk saya",
        cv_data=fake_cv,
        openai_client=client,
    )
    print(f"  Response: {result[:150]}...")
    assert len(result) > 0, "CV Agent returned empty response"


# ── Test 5: CV Agent tanpa CV (harus encourage upload) ───────────────────

def test_cv_agent_no_cv():
    result = handle_cv_query(
        user_message="Saya mau cari kerja yang cocok",
        cv_data=None,
        openai_client=client,
    )
    print(f"  Response: {result[:150]}...")
    assert len(result) > 0, "CV Agent should respond even without CV"


# ── Test 6: Full Flow via run_agent ──────────────────────────────────────

def test_full_flow():
    result = run_agent("Berapa rata-rata gaji di Jakarta?")
    print(f"  Intent: {result['intent']} | Source: {result['source']}")
    print(f"  Response: {result['response'][:150]}...")
    assert result["intent"] == "sql", f"Expected sql, got {result['intent']}"
    assert len(result["response"]) > 0, "Response should not be empty"


# ── Test 7: Hybrid ───────────────────────────────────────────────────────

def test_hybrid():
    result = run_agent("Cari lowongan data scientist yang gajinya di atas 10 juta")
    print(f"  Intent: {result['intent']} | Source: {result['source']}")
    print(f"  Response: {result['response'][:150]}...")
    assert result["intent"] == "hybrid", f"Expected hybrid, got {result['intent']}"
    assert len(result["response"]) > 0, "Hybrid response should not be empty"


# ── Test 8: Chat ─────────────────────────────────────────────────────────

def test_chat():
    result = run_agent("Halo, terima kasih ya!")
    print(f"  Intent: {result['intent']} | Source: {result['source']}")
    print(f"  Response: {result['response'][:150]}...")
    assert result["intent"] == "chat", f"Expected chat, got {result['intent']}"


# ── Run All Tests ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "🔥" * 20)
    print("  MULTI-AGENT SYSTEM — FULL TEST SUITE")
    print("🔥" * 20)

    test("1. Main Agent Routing", test_routing)
    test("2. SQL Agent", test_sql_agent)
    test("3. RAG Agent + Citation", test_rag_agent)
    test("4. CV Agent (with CV)", test_cv_agent)
    test("5. CV Agent (no CV)", test_cv_agent_no_cv)
    test("6. Full Flow (run_agent)", test_full_flow)
    test("7. Hybrid Answer", test_hybrid)
    test("8. Chat Handler", test_chat)

    print(f"\n{'=' * 60}")
    print(f"TOTAL: {passed} passed ✅ | {failed} failed ❌ | {passed + failed} total")
    print(f"{'=' * 60}")
