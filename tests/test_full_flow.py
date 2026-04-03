"""
test_full_flow.py
Test Main Agent routing to all agents in one go
"""

from backend.app.agents.main_agent import run_agent

tests = [
    ("Berapa jumlah lowongan remote di database?", None),
    ("Cari lowongan frontend developer", None),
    ("Halo apa kabar?", None),
]

print("=" * 60)
print("FULL FLOW TEST")
print("=" * 60)

for msg, cv in tests:
    result = run_agent(msg, cv)
    source = result["source"]
    intent = result["intent"]
    response = result["response"][:200]
    print(f"\n[{source}] intent: {intent}")
    print(f"Q: {msg}")
    print(f"A: {response}...")
    print("-" * 60)

print("\nDone!")