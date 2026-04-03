"""
test_hybrid.py
Test improved routing + hybrid answers
"""

from backend.app.agents.main_agent import run_agent

tests = [
    "Cari lowongan data scientist yang gajinya di atas 10 juta",
    "Lowongan remote di bidang AI, berapa rata-rata gajinya?",
    "Berapa jumlah lowongan di Jakarta?",
    "Ceritakan tentang lowongan frontend developer",
    "Halo!",
]

for msg in tests:
    print("=" * 60)
    result = run_agent(msg)
    print(f"Intent: {result['intent']} | Source: {result['source']}")
    print(f"Q: {msg}")
    print(f"A: {result['response'][:200]}...")
    print()