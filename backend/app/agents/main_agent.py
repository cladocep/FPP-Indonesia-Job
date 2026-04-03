"""
agents/main_agent.py

Main Agent (Orchestrator / Router)

The "brain" of the multi-agent system.
Receives user input → classifies intent → routes to the correct agent.

Intent categories:
- "rag"    → questions about job descriptions, companies, skills (semantic)
- "sql"    → questions about numbers, counts, salary ranges, statistics
- "cv"     → CV upload, job recommendation, career consultation
- "hybrid" → questions that need BOTH rag + sql (e.g. "cari lowongan ML dengan gaji di atas 10 juta")
- "chat"   → general conversation, greetings, off-topic
"""

from openai import OpenAI

from backend.app.config import OPENAI_API_KEY, LLM_MODEL
from backend.app.agents.rag_agent import handle_rag_query
from backend.app.agents.sql_agent import handle_sql_query
from backend.app.agents.cv_agent import handle_cv_query


# ── intent classification ────────────────────────────────────────────────────

ROUTER_SYSTEM_PROMPT = """You are a routing assistant for an Indonesian Job Search system.

Your ONLY job is to classify the user's intent into one of these categories:

- "rag" → user asks about job descriptions, responsibilities, requirements, company info, what skills are needed for a role, or wants to find/search jobs by description. Semantic/descriptive questions.
  Examples: "Ceritakan tentang lowongan data scientist", "Apa skill yang dibutuhkan frontend developer?", "Cari lowongan di bidang marketing"

- "sql" → user asks about numbers, counts, statistics, salary ranges, comparisons, averages, top/bottom lists, distributions. Data/quantitative questions.
  Examples: "Berapa jumlah lowongan di Jakarta?", "Rata-rata gaji data analyst?", "Kota mana yang paling banyak lowongan?"

- "cv" → user uploads a CV, asks for job recommendations based on their profile, wants career consultation, skill gap analysis, or career advice.
  Examples: "Rekomendasikan pekerjaan berdasarkan CV saya", "Analisis skill gap saya", "Saran karir untuk saya"

- "hybrid" → user asks a question that combines BOTH descriptive search AND quantitative data. The question needs information from documents AND database statistics.
  Examples: "Cari lowongan data scientist yang gajinya di atas 10 juta", "Lowongan remote di bidang AI, berapa rata-rata gajinya?", "Rekomendasikan lowongan ML di Jakarta dengan gaji tertinggi"

- "chat" → greetings, thank you, off-topic, or general conversation not related to jobs.
  Examples: "Halo", "Terima kasih", "Siapa kamu?"

Decision rules:
1. If the question mentions BOTH a specific role/skill/description AND salary/count/statistics → "hybrid"
2. If the question is purely about finding or describing jobs → "rag"
3. If the question is purely about numbers or data → "sql"
4. If it mentions CV, recommendation, career advice → "cv"
5. Otherwise → "chat"

Respond with ONLY the category name (rag, sql, cv, hybrid, or chat). Nothing else."""


def classify_intent(user_message: str, openai_client: OpenAI = None) -> str:
    """
    Use LLM to classify user intent.

    Returns: "rag", "sql", "cv", "hybrid", or "chat"
    """
    if openai_client is None:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
        max_tokens=10,
    )

    intent = response.choices[0].message.content.strip().lower()

    # Validate — fallback to "chat" if unexpected
    if intent not in ("rag", "sql", "cv", "hybrid", "chat"):
        intent = "chat"

    return intent


# ── chat handler ─────────────────────────────────────────────────────────────

def handle_chat(user_message: str, openai_client: OpenAI = None) -> str:
    """Handle general conversation / greetings."""
    if openai_client is None:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a friendly AI assistant for an Indonesian Job Search platform. "
                    "Respond in the same language the user uses (Indonesian or English). "
                    "Be helpful and guide users to ask about jobs, upload their CV, "
                    "or ask about salary/statistics."
                ),
            },
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=500,
    )

    return response.choices[0].message.content


# ── hybrid handler ───────────────────────────────────────────────────────────

def handle_hybrid_query(user_message: str, openai_client: OpenAI = None) -> str:
    """
    Handle hybrid queries that need BOTH RAG + SQL.

    Flow:
    1. Run RAG Agent for descriptive/semantic results
    2. Run SQL Agent for quantitative data
    3. Combine both answers using LLM
    """
    if openai_client is None:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)

    print(f"[Hybrid] Running RAG Agent...")
    rag_result = handle_rag_query(user_message, openai_client)

    print(f"[Hybrid] Running SQL Agent...")
    sql_result = handle_sql_query(user_message, openai_client)

    # Combine both results
    print(f"[Hybrid] Combining results...")
    combine_prompt = f"""You are a helpful assistant that combines information from two sources into one clear answer.

The user asked: "{user_message}"

Source 1 (Job descriptions & semantic search):
{rag_result}

Source 2 (Database statistics & numbers):
{sql_result}

Combine both sources into ONE comprehensive answer.
Rules:
1. Merge the information naturally — don't say "Source 1 says..." or "Source 2 says..."
2. Lead with the most relevant information
3. Include both descriptive details AND quantitative data
4. Respond in the same language the user uses (Indonesian or English)
5. Keep source citations if available from Source 1"""

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": combine_prompt},
        ],
        temperature=0.3,
        max_tokens=1500,
    )

    return response.choices[0].message.content


# ── main orchestrator ────────────────────────────────────────────────────────

def run_agent(user_message: str, cv_data: dict = None) -> dict:
    """
    Main entry point for the multi-agent system.

    Args:
        user_message: the user's question or request
        cv_data: optional parsed CV data (from CV parser)

    Returns:
        dict with keys:
            - intent: classified intent
            - response: the agent's answer
            - source: which agent handled it
    """
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    # Step 1: Classify intent
    if cv_data:
        intent = "cv"
    else:
        intent = classify_intent(user_message, openai_client)

    print(f"[Main Agent] Intent: {intent} | Message: {user_message[:80]}...")

    # Step 2: Route to the correct agent
    try:
        if intent == "rag":
            response = handle_rag_query(user_message, openai_client)
            source = "RAG Agent"

        elif intent == "sql":
            response = handle_sql_query(user_message, openai_client)
            source = "SQL Agent"

        elif intent == "cv":
            response = handle_cv_query(user_message, cv_data, openai_client)
            source = "CV Agent"

        elif intent == "hybrid":
            response = handle_hybrid_query(user_message, openai_client)
            source = "Hybrid (RAG + SQL)"

        else:  # chat
            response = handle_chat(user_message, openai_client)
            source = "Chat"

    except Exception as e:
        print(f"[Main Agent] Error in {intent} agent: {e}")
        response = (
            "Maaf, terjadi kesalahan saat memproses pertanyaan kamu. "
            "Coba tanya dengan cara yang berbeda ya!"
        )
        source = "Error"

    return {
        "intent": intent,
        "response": response,
        "source": source,
    }
