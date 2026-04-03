"""
test_routing.py
Quick test for Main Agent intent classification
"""

from backend.app.agents.main_agent import classify_intent
from openai import OpenAI
from backend.app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

# Tambahin pertanyaan sesuka kamu di sini!
tests = [
    "Berapa jumlah lowongan di Jakarta?",
    "Ceritakan tentang lowongan data scientist",
    "Rekomendasikan pekerjaan berdasarkan CV saya",
    "Halo, apa kabar?",
    "Rata-rata gaji di Bandung berapa?",
    "Apa saja skill yang dibutuhkan frontend developer?",
    "Tolong analisis skill gap dari CV saya",
    "Kota mana yang paling banyak lowongan?",
    "Aku mau cari kerja remote di bidang marketing",
    "Terima kasih banyak ya!",
]

print("=" * 60)
print("MAIN AGENT ROUTING TEST")
print("=" * 60)

for msg in tests:
    intent = classify_intent(msg, client)
    print(f"  {intent:5s}  |  {msg}")

print("=" * 60)
print("Done!")