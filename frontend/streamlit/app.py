"""
FPP Indonesia Job Search - Modern Streamlit Frontend
"""

import streamlit as st
import requests
from typing import Optional, List, Dict
import json
import os

# ═══════════════════════════════════════════════════════
# API CLIENT CLASS
# ═══════════════════════════════════════════════════════

class APIClient:
    """API Client untuk koneksi ke backend FastAPI"""
    
    def __init__(self, base_url: str = None):
        # Get from environment variable jika ada
        if base_url is None:
            base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        
        self.base_url = base_url
        self.timeout = 60  # ADD THIS LINE
        print(f"[DEBUG] APIClient initialized with base_url: {self.base_url}", flush=True)
    
    def is_connected(self):
        """Check koneksi ke backend"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            is_ok = response.status_code == 200
            print(f"[DEBUG] Backend health check: {response.status_code}", flush=True)
            return is_ok
        except Exception as e:
            print(f"[DEBUG] Backend connection error: {str(e)}", flush=True)
            return False
    
    def send_message(self, user_id: str, message: str, session_id: Optional[str] = None) -> Dict:
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={"message": message},
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def send_message_stream(self, user_id: str, message: str):
        """Stream chat response as Server-Sent Events. Yields parsed event dicts."""
        try:
            response = requests.post(
                f"{self.base_url}/chat/stream",
                json={"message": message},
                stream=True,
                timeout=60
            )
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    try:
                        yield json.loads(line[6:])
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            yield {"type": "error", "message": str(e)}
    
    def analyze_cv(self, file_content: bytes, filename: str) -> Dict:
        try:
            files = {"file": (filename, file_content)}
            response = requests.post(
                f"{self.base_url}/api/cv/analyze", 
                files=files, 
                timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_recommendations(self, skills: List[str], location: str, roles: Optional[List[str]] = None) -> Dict:
        try:
            response = requests.post(
                f"{self.base_url}/api/recommendations/personalized",
                json={"current_skills": skills, "desired_roles": roles or [], "location": location},
                timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_career_advice(self, current_role: str, target_role: str, skills: List[str], experience: int) -> Dict:
        try:
            response = requests.post(
                f"{self.base_url}/api/consultation/career-advice",
                json={"current_role": current_role, "target_role": target_role, "current_skills": skills, "years_experience": experience},
                timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}


# ═══════════════════════════════════════════════════════
# PAGE CONFIG & STYLING
# ═══════════════════════════════════════════════════════

st.set_page_config(
    page_title="FPP Indonesia Job Search",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state variables
if "user_id" not in st.session_state:
    import uuid
    st.session_state.user_id = str(uuid.uuid4())

st.markdown("""
<style>
    /* Modern & Clean Design - Light Blue Background */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #e6f2ff 0%, #f0f8ff 100%);
    }

    .main {
        background: linear-gradient(135deg, #e6f2ff 0%, #f0f8ff 100%);
        padding: 0;
    }

    /* TRY ASKING container - white background */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white !important;
        border: 1px solid #d1d5db !important;
        border-radius: 12px !important;
    }

    /* Chat input - white background + outline */
    [data-testid="stTextInput"] input {
        background-color: white !important;
        border: 1.5px solid #d1d5db !important;
        border-radius: 8px !important;
    }
    [data-testid="stTextInput"] input:focus {
        border-color: #0066cc !important;
        box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.15) !important;
    }

    /* Send button - solid blue */
    [data-testid="stFormSubmitButton"] button {
        background-color: #0066cc !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    [data-testid="stFormSubmitButton"] button:hover {
        background-color: #0052a3 !important;
    }
    
    /* Header - Full Blue */
    .header-section {
        background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%);
        padding: 50px 40px;
        border-bottom: none;
        margin-bottom: 30px;
    }
    
    .header-section h1 {
        margin: 0;
        font-size: 42px;
        font-weight: 700;
        color: #ffffff;
    }
    
    .header-section h2 {
        margin: 0;
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
    }
    
    .header-section p {
        margin: 12px 0 0 0;
        font-size: 16px;
        color: #ffffff;
        opacity: 0.95;
    }
    
    /* Cards - Full Blue */
    .card {
        background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%);
        padding: 24px;
        border-radius: 8px;
        border: none;
        margin: 15px 0;
        box-shadow: 0 2px 8px rgba(0, 102, 204, 0.15);
        transition: all 0.2s ease;
        color: white;
    }
    
    .card:hover {
        box-shadow: 0 4px 16px rgba(0, 102, 204, 0.25);
        transform: translateY(-2px);
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #0066cc;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background-color: #0052a3;
        box-shadow: 0 4px 12px rgba(0, 102, 204, 0.3);
    }

    /* Metrics */
    .metric-box {
        background: white;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        text-align: center;
    }
    
    /* Custom tab bar link hover */
    .custom-tab-bar a:hover {
        color: #0066cc !important;
        background: #f0f8ff !important;
    }

    /* Smooth fade-in for tab content */
    @keyframes tabFadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .tab-content-wrapper {
        animation: tabFadeIn 0.18s ease;
    }

    /* Multiselect & Input Styling - Neon Green */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #c8ff00 !important;
        color: #0052a3 !important;
        border-radius: 20px !important;
        font-weight: 600 !important;
    }
    
    .stMultiSelect [data-baseweb="tag"] svg {
        color: #0052a3 !important;
    }
    
    .stNumberInput input {
        border-radius: 8px !important;
        border: 2px solid #c8ff00 !important;
    }
    
    .stNumberInput input:focus {
        border-color: #0066cc !important;
        box-shadow: 0 0 0 3px rgba(200, 255, 0, 0.1) !important;
    }
    
    /* Select Dropdown - Neon Highlight */
    [data-baseweb="select"] {
        border-radius: 8px !important;
    }
    
    [data-baseweb="select"] button {
        border: 2px solid #c8ff00 !important;
        border-radius: 8px !important;
    }
    
    /* Labels styling */
    label {
        color: #0a2540 !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize APIClient dengan environment variable atau default
api_client = APIClient()

# ═══════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════

# HEADER section:
_backend_online = api_client.is_connected()
_status_color = "#16a34a" if _backend_online else "#dc2626"
_status_label = "Online" if _backend_online else "Offline"
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 16px 40px; background: white; border-bottom: 1px solid #e5e7eb;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Crect fill='%230066cc' width='40' height='40' rx='8'/%3E%3Ctext x='50%25' y='50%25' font-size='24' font-weight='700' fill='white' text-anchor='middle' dy='.3em'%3EFPP%3C/text%3E%3C/svg%3E" style="width: 32px; height: 32px;">
        <div style="font-size: 18px; font-weight: 700; color: #0066cc;">FPP Indonesia Job Search</div>
    </div>
    <div style="font-size: 12px; color: #999;">
        Status: <span style="color: {_status_color};">● {_status_label}</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# MAIN NAVIGATION - Session-state based (no flash)
# ═══════════════════════════════════════════════════════

# Read ?tab=N query param and persist in session state
_param_tab = st.query_params.get("tab", None)
if _param_tab is not None:
    try:
        st.session_state.active_tab = int(_param_tab)
    except (ValueError, TypeError):
        pass

if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0

_active = st.session_state.active_tab

# Custom HTML tab bar (links set ?tab=N, Python reads it on next render)
_tab_items = ["Home", "Chat AI", "CV Analysis", "Job Match", "Career Path"]
_bar = ['<div class="custom-tab-bar" style="display:flex; justify-content:center; background:white; border-bottom:2px solid #e5e7eb; padding:0; margin-bottom:0;">']
for _i, _name in enumerate(_tab_items):
    _on = _i == _active
    _bar.append(
        f'<a href="?tab={_i}" target="_self" style="display:inline-block; padding:14px 22px; '
        f'text-decoration:none; font-weight:{"700" if _on else "500"}; '
        f'color:{"#0066cc" if _on else "#4a5568"}; '
        f'border-bottom:{"3px solid #0066cc" if _on else "3px solid transparent"}; '
        f'background:white; transition:color 0.15s,border-color 0.15s;">{_name}</a>'
    )
_bar.append('</div>')
st.markdown("".join(_bar), unsafe_allow_html=True)

# Wrap all content in the fade-in div
st.markdown('<div class="tab-content-wrapper">', unsafe_allow_html=True)

if _active == 0:
    # HOME CONTENT
    col1, col2 = st.columns([2, 1], gap="large")
    
    with col1:
        st.markdown("""
        <div style="padding: 20px 0 8px 0;">
            <h1 style="margin: 0 0 12px 0; font-size: 48px; font-weight: 700; color: #0a2540; line-height: 1.2;">
                Smarter Job Search, Better Results
            </h1>
            <p style="margin: 0 0 16px 0; font-size: 18px; color: #666; line-height: 1.6;">
                Leverage AI to discover the right opportunities and accelerate your career
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(
            '<div style="display:flex; gap:12px; margin-top:8px;">'
            '<a href="?tab=1" target="_self" style="display:inline-block; background:#c8ff00; color:#0052a3;'
            ' padding:12px 28px; border-radius:24px; font-weight:700; text-decoration:none; font-size:14px;">Chat with AI</a>'
            '<a href="?tab=2" target="_self" style="display:inline-block; background:white; color:#0066cc;'
            ' padding:12px 28px; border-radius:24px; font-weight:700; text-decoration:none;'
            ' border:2px solid #0066cc; font-size:14px;">Analyze My CV</a>'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown("""
        <div style="margin-top: 16px; background: white; border: 1px solid #e5e7eb; padding: 16px 20px; border-radius: 8px; display: inline-block; font-size: 13px; color: #666;">
            <span style="font-weight: 600; color: #0a2540;">TRUSTED BY 399+ Companies </span> • Waiting for You to Join Them!
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div style='margin-top: 80px;'>", unsafe_allow_html=True)
        st.markdown("### Quick Stats")
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("Opportunities Available", "470+")
        with col_stat2:
            st.metric("Job Match Rate", "95%")
        with col_stat1:
            st.metric("Avg. Match Time", "2 min")
        with col_stat2:
            st.metric("Locations Across Indonesia", "80+")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    
    st.markdown("### One Stop for Your Career Journey")
    
    # Row 1
    feat_col1, feat_col2 = st.columns(2, gap="large")
    
    with feat_col1:
        st.markdown("""
        <div style="background: white; border: 1px solid #e5e7eb; padding: 24px; border-radius: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: all 0.2s ease;">
            <b style="color: #0a2540; display: block; font-size: 16px;">Chat AI Assistant</b>
            <p style="color: #666; font-size: 13px; margin-top: 8px; line-height: 1.5;">Ask questions about jobs, salaries, and career growth</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col2:
        st.markdown("""
        <div style="background: white; border: 1px solid #e5e7eb; padding: 24px; border-radius: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: all 0.2s ease;">
            <b style="color: #0a2540; display: block; font-size: 16px;">Define Your Target Role</b>
            <p style="color: #666; font-size: 13px; margin-top: 8px; line-height: 1.5;">Find jobs that align with your goals and skills</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Row 2
    feat_col3, feat_col4 = st.columns(2, gap="large")
    
    with feat_col3:
        st.markdown("""
        <div style="background: white; border: 1px solid #e5e7eb; padding: 24px; border-radius: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: all 0.2s ease;">
            <b style="color: #0a2540; display: block; font-size: 16px;">CV Analysis</b>
            <p style="color: #666; font-size: 13px; margin-top: 8px; line-height: 1.5;">Get detailed feedback on your resume and improvements</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col4:
        st.markdown("""
        <div style="background: white; border: 1px solid #e5e7eb; padding: 24px; border-radius: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: all 0.2s ease;">
            <b style="color: #0a2540; display: block; font-size: 16px;">Job Recommendations</b>
            <p style="color: #666; font-size: 13px; margin-top: 8px; line-height: 1.5;">Discover jobs perfectly matched to your profile</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Row 3
    feat_col5, feat_col6 = st.columns(2, gap="large")
    
    with feat_col5:
        st.markdown("""
        <div style="background: white; border: 1px solid #e5e7eb; padding: 24px; border-radius: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: all 0.2s ease;">
            <b style="color: #0a2540; display: block; font-size: 16px;">Smart Location Matching</b>
            <p style="color: #666; font-size: 13px; margin-top: 8px; line-height: 1.5;">Find opportunities around your location</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col6:
        st.markdown("""
        <div style="background: white; border: 1px solid #e5e7eb; padding: 24px; border-radius: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: all 0.2s ease;">
            <b style="color: #0a2540; display: block; font-size: 16px;">Career Development</b>
            <p style="color: #666; font-size: 13px; margin-top: 8px; line-height: 1.5;">Get personalized growth path and skill recommendations</p>
        </div>
        """, unsafe_allow_html=True)

elif _active == 1:
    # CHAT CONTENT (copy dari elif _active == 1)
    st.markdown("## Chat with AI Assistant")
    st.markdown("Ask me anything about your career")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("Clear", key="clear_chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    st.markdown("---")

    # Chat display - native st.chat_message (no HTML injection risk)
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.write(message["content"])
                st.caption(f"Source: {message.get('source', 'General')}  •  Intent: {message.get('intent', 'Unknown')}")

    # Handle pending message — streaming
    pending = st.session_state.get("pending_prompt")
    if pending:
        del st.session_state["pending_prompt"]
        if api_client.is_connected():
            full_response = ""
            source = "General"
            intent = "chat"

            with st.chat_message("assistant", avatar="🤖"):
                placeholder = st.empty()
                for event in api_client.send_message_stream(st.session_state.user_id, pending):
                    if event.get("type") == "meta":
                        source = event.get("source", "General")
                        intent = event.get("intent", "chat")
                    elif event.get("type") == "token":
                        full_response += event.get("content", "")
                        placeholder.write(full_response + "▌")
                    elif event.get("type") == "done":
                        placeholder.write(full_response)
                    elif event.get("type") == "error":
                        placeholder.error(f"Error: {event.get('message', 'Unknown error')}")
                st.caption(f"Source: {source}  •  Intent: {intent}")

            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "source": source,
                "intent": intent,
            })
            st.rerun()
        else:
            st.error("Backend offline — cannot get response.")
    
    # ── Input bar container (TRY ASKING + buttons + input) ───────────────────
    with st.container(border=True):
        st.markdown('<p style="font-size:11px; font-weight:600; color:#999; letter-spacing:1px; margin:0 0 4px 0;">TRY ASKING</p>', unsafe_allow_html=True)

        quick_q = [
            ("Backend jobs", "Show me backend developer jobs in Jakarta"),
            ("Salary range", "What's the average salary for Digital Marketing?"),
            ("Skill gap", "What skills should I learn next?"),
            ("Career tips", "Give me career development advice")
        ]

        q_cols = st.columns(4, gap="small")
        for i, (label, q) in enumerate(quick_q):
            with q_cols[i]:
                if st.button(label, key=f"q_{i}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": q})
                    st.session_state["pending_prompt"] = q
                    st.rerun()

        with st.form(key="chat_form", clear_on_submit=True):
            input_col, send_col = st.columns([5, 1])
            with input_col:
                prompt = st.text_input("e.g., backend jobs or salary info", placeholder="Ask me anything...", label_visibility="collapsed", key="chat_input")
            with send_col:
                submitted = st.form_submit_button("Send", use_container_width=True)
            if submitted and prompt:
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state["pending_prompt"] = prompt
                st.rerun()

elif _active == 2:
    # CV ANALYSIS CONTENT (copy dari elif _active == 2)
    st.markdown("## Upload & Analyze Your CV")
    st.markdown("Get instant feedback on your resume quality and recommendations for improvement")
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1], gap="large")
    
    with col1:
        st.markdown("### Upload Your CV")
        uploaded_file = st.file_uploader("Choose PDF or TXT", type=["pdf", "txt"], key="cv_file")
        
        if uploaded_file and st.button("Analyze", use_container_width=True, key="analyze_cv"):
            with st.spinner("Analyzing..."):
                result = api_client.analyze_cv(uploaded_file.read(), uploaded_file.name)
                if "error" not in result:
                    score = result.get("overall_score", 75)
                    
                    # Determine color based on score
                    if score >= 80:
                        score_color = "#16a34a"  # Green
                        score_label = "Excellent"
                    elif score >= 60:
                        score_color = "#eab308"  # Yellow
                        score_label = "Good"
                    else:
                        score_color = "#dc2626"  # Red
                        score_label = "Needs Improvement"
                    
                    st.success("Analysis Complete!")
                    
                    col_a, col_b, col_c, col_d = st.columns(4)
                    with col_a:
                        st.markdown(f"""
                        <div style="background: white; padding: 16px; border-radius: 8px; text-align: center; border: 2px solid {score_color};">
                            <div style="font-size: 48px; font-weight: 700; color: {score_color};">{score:.0f}</div>
                            <div style="font-size: 20px; color: {score_color}; margin-top: 4px;">%</div>
                            <div style="font-size: 12px; color: #666; margin-top: 8px;">Overall Score</div>
                            <div style="font-size: 11px; color: {score_color}; font-weight: 600; margin-top: 4px;">{score_label}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_b:
                        st.metric("Strengths", len(result.get("strengths", [])))
                    with col_c:
                        st.metric("Improvements", len(result.get("weaknesses", [])))
                    with col_d:
                        st.metric("Recommendations", len(result.get("recommendations", [])))
                    
                    st.markdown("---")
                    
                    col_s, col_w = st.columns(2)
                    with col_s:
                        st.markdown("**Strengths:**")
                        for s in result.get("strengths", []):
                            st.write(f"• {s}")
                    
                    with col_w:
                        st.markdown("**Improvements:**")
                        for w in result.get("weaknesses", []):
                            st.write(f"• {w}")
                    
                    st.markdown("---")
                    
                    st.markdown("**Recommendations:**")
                    for r in result.get("recommendations", []):
                        st.info(r)
    
    with col2:
        st.markdown("### Why Analyze?")
        st.markdown("""
        • **Fix Issues** - Identify resume problems
        
        • **Improve Score** - Get actionable tips
        
        • **Match Better** - Increase job match rate
        
        • **Stand Out** - Make better first impression
        """)

elif _active == 3:
    # JOB MATCH CONTENT (copy dari elif _active == 3)
    st.markdown("## Find Matching Jobs")
    st.markdown("Discover opportunities that match your skills and preferences")

    st.markdown("---")

    # Session state untuk custom entries
    if "custom_skills" not in st.session_state:
        st.session_state.custom_skills = []
    if "custom_locations" not in st.session_state:
        st.session_state.custom_locations = []
    if "custom_roles" not in st.session_state:
        st.session_state.custom_roles = []

    _skills_preset = [
        "Python", "JavaScript", "TypeScript", "Go", "Java", "Kotlin",
        "C++", "C#", "PHP", "Ruby", "Rust", "Swift",
        "React", "Vue.js", "Angular", "Next.js", "FastAPI", "Django",
        "Flask", "Spring Boot", "Node.js", "Express.js", "Laravel",
        "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
        "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
        "Power BI", "Tableau", "Spark", "Hadoop",
        "Docker", "Kubernetes", "AWS", "Google Cloud", "Azure",
        "CI/CD", "Terraform", "Linux", "Git",
        "Leadership", "Communication", "Project Management", "Agile", "Scrum",
    ]
    _locations_preset = [
        "Jakarta", "Surabaya", "Bandung", "Medan", "Semarang",
        "Yogyakarta", "Bali", "Makassar", "Palembang", "Tangerang",
        "Bekasi", "Depok", "Bogor", "Malang", "Batam",
        "Remote", "Hybrid",
    ]
    _roles_preset = [
        "Backend Dev", "Frontend Dev", "Full Stack", "Mobile Dev (Android)",
        "Mobile Dev (iOS)", "Data Scientist", "Data Analyst", "Data Engineer",
        "ML Engineer", "DevOps Engineer", "Cloud Engineer", "Site Reliability Engineer",
        "QA Engineer", "Security Engineer", "Product Manager", "UI/UX Designer",
        "System Analyst", "Database Administrator", "IT Consultant",
    ]

    col1, col2, col3 = st.columns(3, gap="large")

    with col1:
        st.markdown("**Your Skills:**")
        _all_skills = _skills_preset + [s for s in st.session_state.custom_skills if s not in _skills_preset]
        skills = st.multiselect(
            "Select skills",
            _all_skills,
            default=["Python"],
            label_visibility="collapsed",
            key="skills_jobmatch"
        )
        _add_skill_col, _btn_skill_col = st.columns([3, 1])
        with _add_skill_col:
            _new_skill = st.text_input("Add custom skill", placeholder="e.g. Dance", label_visibility="collapsed", key="new_skill_input")
        with _btn_skill_col:
            if st.button("+ Add", key="add_skill_btn", use_container_width=True):
                if _new_skill and _new_skill.strip() not in _all_skills:
                    st.session_state.custom_skills.append(_new_skill.strip())
                    st.rerun()

    with col2:
        st.markdown("**Location:**")
        _all_locations = _locations_preset + [l for l in st.session_state.custom_locations if l not in _locations_preset]
        locations = st.multiselect(
            "Select cities",
            _all_locations,
            default=["Jakarta"],
            label_visibility="collapsed",
            key="locations_jobmatch"
        )
        _add_loc_col, _btn_loc_col = st.columns([3, 1])
        with _add_loc_col:
            _new_location = st.text_input("Add custom location", placeholder="e.g. Cirebon", label_visibility="collapsed", key="new_location_input")
        with _btn_loc_col:
            if st.button("+ Add", key="add_location_btn", use_container_width=True):
                if _new_location and _new_location.strip() not in _all_locations:
                    st.session_state.custom_locations.append(_new_location.strip())
                    st.rerun()

    with col3:
        st.markdown("**Target Role:**")
        _all_roles = _roles_preset + [r for r in st.session_state.custom_roles if r not in _roles_preset]
        roles = st.multiselect(
            "Select job types",
            _all_roles,
            default=["Backend Dev"],
            label_visibility="collapsed",
            key="roles_jobmatch"
        )
        _add_role_col, _btn_role_col = st.columns([3, 1])
        with _add_role_col:
            _new_role = st.text_input("Add custom role", placeholder="e.g. Dance Instructor", label_visibility="collapsed", key="new_role_input")
        with _btn_role_col:
            if st.button("+ Add", key="add_role_btn", use_container_width=True):
                if _new_role and _new_role.strip() not in _all_roles:
                    st.session_state.custom_roles.append(_new_role.strip())
                    st.rerun()
    
    if st.button("Search Jobs", use_container_width=True, key="search_jobs"):
        if skills and locations and roles:
            with st.spinner("Searching..."):
                # Combine locations & roles untuk API call
                location_str = ", ".join(locations)
                result = api_client.get_recommendations(skills, location_str, roles)
                if "error" not in result:
                    jobs = result.get("recommendations", [])[:3]
                    
                    st.markdown(f"### Found {len(jobs)} Matching Jobs")
                    
                    for idx, job in enumerate(jobs, 1):
                        match = job.get("skill_match_percentage", 0)
                        badge = "Great Match" if match >= 80 else "Good Match" if match >= 60 else "Possible Match"
                        
                        st.markdown(f"""
                        <div class="card">
                            <div style="display: flex; justify-content: space-between; align-items: start;">
                                <div>
                                    <div style="font-size: 18px; font-weight: 700; color: #ffff;">
                                        {job.get('job_title', 'Job Title')}
                                    </div>
                                    <div style="color: #ffff; font-size: 14px;">
                                        {job.get('company', 'Company')} • {job.get('location', 'Location')}
                                    </div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 24px; font-weight: bold; color: #ffff;">
                                        {match:.0f}%
                                    </div>
                                    <div style="font-size: 12px; color: #ffff;">Match</div>
                                </div>
                            </div>
                            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #e5e7eb;">
                                {badge}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.warning("Please select at least one skill, location, and role")

elif _active == 4:
    # CAREER PATH CONTENT (copy dari elif _active == 4)
    st.markdown("## Career Development Plan")
    st.markdown("Get personalized career guidance and growth recommendations")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("**Current Role:**")
        current = st.multiselect(
            "Select current role(s)",
            [
                "Junior Developer", "Mid-Level Developer", "Senior Developer",
                "Junior Backend Dev", "Senior Backend Dev", "Frontend Dev",
                "Full Stack Dev", "Mobile Developer", "Data Scientist",
                "Data Analyst", "DevOps Engineer", "Cloud Engineer",
                "QA Engineer", "Security Engineer", "Product Manager",
                "Tech Lead", "Engineering Manager", "Consultant",
            ],
            default=["Junior Developer"],
            label_visibility="collapsed",
            key="current_role"
        )
        
        st.markdown("**Target Role:**")
        target = st.multiselect(
            "Select target role(s)",
            [
                "Mid-Level Developer", "Senior Developer", "Tech Lead",
                "Engineering Manager", "Senior Backend Dev", "Senior Frontend Dev",
                "Full Stack Lead", "Data Scientist", "ML Engineer",
                "DevOps Lead", "Cloud Architect", "Security Lead",
                "Product Manager", "Director of Engineering", "Consultant",
            ],
            default=["Senior Developer"],
            label_visibility="collapsed",
            key="target_role"
        )
    
    with col2:
        st.markdown("**Experience & Skills:**")
        exp = st.number_input("Years of Experience", min_value=0, max_value=50, value=0, key="experience")
        
        st.markdown("**Your Skills:**")
        skills = st.multiselect(
            "Select skills",
            [
                # Programming languages
                "Python", "JavaScript", "TypeScript", "Go", "Java", "Kotlin",
                "C++", "C#", "PHP", "Ruby", "Rust", "Swift",
                # Web & frameworks
                "React", "Vue.js", "Angular", "Next.js", "FastAPI", "Django",
                "Flask", "Spring Boot", "Node.js", "Express.js", "Laravel",
                # Data & ML
                "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
                "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
                "Power BI", "Tableau", "Spark", "Hadoop",
                # DevOps & Cloud
                "Docker", "Kubernetes", "AWS", "Google Cloud", "Azure",
                "CI/CD", "Terraform", "Linux", "Git",
                # Business & soft skills
                "Leadership", "Communication", "Project Management",
                "Agile", "Scrum", "Strategic Planning", "Budgeting",
                "Stakeholder Management", "Data Analysis", "Excel",
            ],
            default=["Communication"],
            label_visibility="collapsed",
            key="skills_career"
        )
    
    if st.button("Get Career Advice", use_container_width=True, key="career_advice"):
        if current and target and skills:
            with st.spinner("Analyzing..."):
                # Combine multiple roles
                current_str = ", ".join(current)
                target_str = ", ".join(target)
                
                result = api_client.get_career_advice(current_str, target_str, skills, exp)
                if "error" not in result:
                    st.success("Career plan created!")
                    
                    if result.get("career_advice"):
                        st.info(result["career_advice"])

                    st.markdown(f"""
                    <div class="card">
                        <b>Current Role(s):</b> {current_str}<br>
                        <b>Target Role(s):</b> {target_str}<br>
                        <b>Timeline:</b> {result.get("timeline", "12-24 months")}<br>
                        <b>Effort Required:</b> {result.get("effort", "Moderate")}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("**Recommended Skills to Learn:**")
                    for rec in result.get("recommendations", [])[:6]:
                        st.write(f"• {rec}")
                    
                    st.markdown("---")
                    
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("Skills Owned", len(skills))
                    with col_stat2:
                        st.metric("To Learn", len(result.get("recommendations", [])))
                    with col_stat3:
                        pct = int((len(skills) / (len(skills) + len(result.get("recommendations", [])))) * 100) if skills else 0
                        st.metric("Progress", f"{pct}%")
        else:
            st.warning("⚠️ Please select at least one current role, target role, and skill")

st.markdown('</div>', unsafe_allow_html=True)  # close tab-content-wrapper

# ═══════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════

st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px 0; color: #666; font-size: 13px;">
    <p>© 2026 FPP Indonesia Job Search. Connecting Talent with Opportunity</p>
    <p>Made with care for Indonesia Job Seekers</p>
</div>
""", unsafe_allow_html=True)
