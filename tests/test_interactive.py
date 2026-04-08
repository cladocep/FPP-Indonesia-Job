"""
test_interactive.py

Interactive test for SQL and RAG agents.
Write your own questions and see the agent responses in real time.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.agents.rag_agent import handle_rag_query
from backend.app.agents.sql_agent import handle_sql_query
from backend.app.config import OPENAI_API_KEY
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

MENU = """
==============================
  INTERACTIVE AGENT TESTER
==============================
Choose agent:
  1. SQL Agent  (data/statistics questions)
  2. RAG Agent  (job description/search questions)
  3. Exit
------------------------------
"""

def run_sql(question):
    print("\n[SQL Agent] Processing...")
    result = handle_sql_query(question, client)
    print(f"\nResponse:\n{result}\n")

def run_rag(question):
    print("\n[RAG Agent] Processing...")
    result = handle_rag_query(question, client)
    print(f"\nResponse:\n{result}\n")

if __name__ == "__main__":
    print(MENU)
    while True:
        choice = input("Select agent (1/2/3): ").strip()

        if choice == "3":
            print("Exiting. Goodbye!")
            break
        elif choice == "1":
            question = input("Your question for SQL Agent: ").strip()
            if question:
                run_sql(question)
        elif choice == "2":
            question = input("Your question for RAG Agent: ").strip()
            if question:
                run_rag(question)
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

        print(MENU)
