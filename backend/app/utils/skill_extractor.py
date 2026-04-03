"""
utils/skill_extractor.py

Skill extraction utilities for the Multi-Agent System.
Extracts structured skill lists from raw job description or CV text.
Must stay in sync with prepare_data.py SKILL_PATTERNS.
"""

import re


# ── skill patterns ────────────────────────────────────────────────────────────

SKILL_PATTERNS: dict[str, list[str]] = {
    "sql": [r"\bsql\b", r"\bmysql\b", r"\bpostgresql\b", r"\bpostgres\b", r"\bsql server\b"],
    "python": [r"\bpython\b"],
    "excel": [r"\bexcel\b", r"\bmicrosoft excel\b"],
    "power bi": [r"\bpower\s?bi\b"],
    "tableau": [r"\btableau\b"],
    "looker": [r"\blooker\b", r"\blooker studio\b", r"\bdata studio\b"],
    "google sheets": [r"\bgoogle sheets\b"],
    "dashboarding": [r"\bdashboard\b", r"\bdashboarding\b", r"\breporting\b"],
    "statistics": [r"\bstatistics\b", r"\bstatistical\b"],
    "machine learning": [r"\bmachine learning\b", r"\bml\b"],
    "data analysis": [r"\bdata analysis\b", r"\bdata analyst\b", r"\banalytical\b"],
    "data visualization": [r"\bdata visualization\b", r"\bvisualization\b"],
    "etl": [r"\betl\b", r"\bdata pipeline\b"],
    "spark": [r"\bspark\b", r"\bpyspark\b"],
    "hadoop": [r"\bhadoop\b"],
    "aws": [r"\baws\b", r"\bamazon web services\b"],
    "gcp": [r"\bgcp\b", r"\bgoogle cloud\b"],
    "azure": [r"\bazure\b"],
    "communication": [r"\bcommunication\b", r"\bcommunicate\b", r"\binterpersonal\b"],
    "presentation": [r"\bpresentation\b", r"\bpresenting\b"],
    "problem solving": [r"\bproblem solving\b", r"\bproblem-solving\b"],
    "leadership": [r"\bleadership\b", r"\blead\b", r"\bteam lead\b"],
    "project management": [r"\bproject management\b", r"\bproject manager\b"],
    "recruitment": [r"\brecruitment\b", r"\brecruiter\b", r"\btalent acquisition\b"],
    "sales": [r"\bsales\b"],
    "marketing": [r"\bmarketing\b", r"\bdigital marketing\b"],
    "customer service": [r"\bcustomer service\b", r"\bcustomer support\b"],
    "accounting": [r"\baccounting\b", r"\baccountant\b"],
    "finance": [r"\bfinance\b", r"\bfinancial\b"],
    "hr": [r"\bhuman resources\b", r"\bhr\b"],
    "canva": [r"\bcanva\b"],
    "figma": [r"\bfigma\b"],
    "javascript": [r"\bjavascript\b", r"\bjs\b"],
    "java": [r"\bjava\b"],
    "c++": [r"\bc\+\+\b"],
    "php": [r"\bphp\b"],
    "laravel": [r"\blaravel\b"],
    "react": [r"\breact\b", r"\breactjs\b", r"\breact\.js\b"],
    "node.js": [r"\bnode\.?js\b", r"\bnodejs\b"],
    "git": [r"\bgit\b", r"\bgithub\b", r"\bgitlab\b"],
    "english": [r"\benglish\b", r"\bfluent in english\b"],
}


# ── extraction ────────────────────────────────────────────────────────────────

def extract_skills(text: str) -> list[str]:
    """
    Extract canonical skill names from raw text.

    Returns a sorted list of unique skills found.
    """
    text_lower = (text or "").strip().lower()
    found = []

    for canonical_skill, patterns in SKILL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                found.append(canonical_skill)
                break

    return sorted(set(found))


def skills_to_csv(skills: list[str]) -> str:
    """Convert a list of skills to a comma-separated string."""
    return ", ".join(skills)


def skills_from_csv(skills_csv: str) -> list[str]:
    """Parse a comma-separated skills string back into a list."""
    if not skills_csv:
        return []
    return [s.strip() for s in skills_csv.split(",") if s.strip()]
