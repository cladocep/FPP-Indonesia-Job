"""
FPP Indonesia Job Search - Modern Streamlit Frontend
"""

import streamlit as st
import requests
from typing import Optional, List, Dict
import json

# ═══════════════════════════════════════════════════════
# API CLIENT CLASS
# ═══════════════════════════════════════════════════════

class APIClient:
    """API Client untuk koneksi ke backend FastAPI"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 10
    
    def is_connected(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def send_message(self, user_id: str, message: str, session_id: Optional[str] = None) -> Dict:
        try:
            response = requests.post(
                f"{self.base_url}/api/chat/message",
                params={"user_id": user_id, "message": message, "session_id": session_id},
                timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_cv(self, file_content: bytes, filename: str) -> Dict:
        try:
            files = {"file": (filename, file_content)}
            response = requests.post(f"{self.base_url}/api/cv/analyze", files=files, timeout=self.timeout)
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
# PAGE CONFIG & STYLING (jobscan-inspired)
# ═══════════════════════════════════════════════════════

st.set_page_config(
    page_title="FPP Indonesia Job Search",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: white;
        border-bottom: 2px solid #e5e7eb;
        gap: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 20px;
        background-color: white;
        border-bottom: 2px solid transparent;
        color: #4a5568;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        color: #0066cc;
        border-bottom-color: #0066cc !important;
    }
</style>
""", unsafe_allow_html=True)

api_client = APIClient("http://localhost:8000")

# ═══════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════

st.markdown("""
<div class="header-section">
    <h1>💼 FPP Indonesia Job Search</h1>
    <p>Find your perfect job with AI-powered skill matching & career guidance</p>
</div>
""", unsafe_allow_html=True)

# Top bar
col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
with col1:
    st.markdown("")
with col2:
    user_id = st.text_input("ID", value="user_123", label_visibility="collapsed", key="user_id_input")
with col3:
    api_status = "🟢 Connected" if api_client.is_connected() else "🔴 Offline"
    st.markdown(f"**Status:** {api_status}")
with col4:
    st.markdown("**v1.0** · Production")

st.markdown("---")

# ═══════════════════════════════════════════════════════
# MAIN NAVIGATION (TABS)
# ═══════════════════════════════════════════════════════

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 Home",
    "💬 Chat AI",
    "📄 CV Analysis",
    "💼 Job Match",
    "💡 Career Path"
])

# ═══════════════════════════════════════════════════════
# TAB 1: HOME
# ═══════════════════════════════════════════════════════

with tab1:
    col1, col2 = st.columns([2, 1], gap="large")
    
    with col1:
        st.markdown("## Get Started with AI Job Matching")
        st.markdown("""
        Optimize your job search with our intelligent platform:
        
        **🤖 Smart Matching** - Find jobs that match your skills and experience
        
        **📊 Skill Analysis** - Understand your strengths and growth areas
        
        **💡 Career Guidance** - Get personalized career development plans
        
        **🚀 Quick Results** - Save time with AI-powered recommendations
        """)
    
    with col2:
        st.markdown("### Quick Stats")
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("Jobs Available", "10,000+")
        with col_stat2:
            st.metric("Success Rate", "94%")
        with col_stat1:
            st.metric("Avg. Match Time", "2 min")
        with col_stat2:
            st.metric("Users Active", "5,000+")
    
    st.markdown("---")
    
    st.markdown("### Core Features")
    feature_col1, feature_col2, feature_col3 = st.columns(3, gap="large")
    
    with feature_col1:
        st.markdown("""
        <div class="card">
            <div style="font-size: 32px; margin-bottom: 10px;">💬</div>
            <b style="color: white; display: block;">Chat AI Assistant</b>
            <p style="color: rgba(255, 255, 255, 0.9); font-size: 13px; margin-top: 8px;">Ask questions about jobs, salaries, and career growth</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_col2:
        st.markdown("""
        <div class="card">
            <div style="font-size: 32px; margin-bottom: 10px;">📄</div>
            <b style="color: white; display: block;">CV Analysis</b>
            <p style="color: rgba(255, 255, 255, 0.9); font-size: 13px; margin-top: 8px;">Get detailed feedback on your resume and improvements</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_col3:
        st.markdown("""
        <div class="card">
            <div style="font-size: 32px; margin-bottom: 10px;">💼</div>
            <b style="color: white; display: block;">Job Recommendations</b>
            <p style="color: rgba(255, 255, 255, 0.9); font-size: 13px; margin-top: 8px;">Discover jobs perfectly matched to your profile</p>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# TAB 2: CHAT
# ═══════════════════════════════════════════════════════

with tab2:
    st.markdown("## Chat with AI Assistant")
    st.markdown("Ask about jobs, careers, salaries, or skill development")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("Clear", key="clear_chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    st.markdown("---")
    
    # Chat display
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div style="margin: 12px 0; display: flex; justify-content: flex-end;">
                <div style="background: #0066cc; color: white; padding: 12px 16px; border-radius: 16px; max-width: 70%; word-wrap: break-word;">
                    {message['content']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="margin: 12px 0; display: flex; justify-content: flex-start;">
                <div style="background: #f0f2f5; padding: 12px 16px; border-radius: 16px; max-width: 70%; word-wrap: break-word;">
                    {message['content']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick questions
    st.markdown("**Quick Questions:**")
    col1, col2, col3, col4 = st.columns(4, gap="small")
    
    quick_q = [
        ("Backend Job", "Show me backend developer jobs in Jakarta"),
        ("Salary Range", "What's the average salary for senior developers?"),
        ("Skill Gap", "What skills should I learn next?"),
        ("Career Tips", "Give me career development advice")
    ]
    
    cols = [col1, col2, col3, col4]
    for i, (label, q) in enumerate(quick_q):
        with cols[i]:
            if st.button(label, key=f"q_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": q})
                if api_client.is_connected():
                    with st.spinner("Processing..."):
                        resp = api_client.send_message(user_id, q)
                        if "error" not in resp:
                            st.session_state.messages.append({"role": "assistant", "content": resp.get("reply", "No response")})
                            st.rerun()
    
    st.markdown("---")
    
    col1, col2 = st.columns([5, 1])
    with col1:
        prompt = st.text_input("Ask me anything...", placeholder="e.g., backend jobs or salary info", label_visibility="collapsed", key="chat_input")
    with col2:
        if st.button("Send", key="send", use_container_width=True):
            if prompt:
                st.session_state.messages.append({"role": "user", "content": prompt})
                if api_client.is_connected():
                    with st.spinner("Processing..."):
                        resp = api_client.send_message(user_id, prompt)
                        if "error" not in resp:
                            st.session_state.messages.append({"role": "assistant", "content": resp.get("reply", "Error")})
                            st.rerun()

# ═══════════════════════════════════════════════════════
# TAB 3: CV ANALYSIS
# ═══════════════════════════════════════════════════════

with tab3:
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
                    
                    st.success(f"✅ Analysis complete - Score: {score}%")
                    
                    col_a, col_b, col_c, col_d = st.columns(4)
                    with col_a:
                        st.metric("Overall", f"{score}%")
                    with col_b:
                        st.metric("Strengths", len(result.get("strengths", [])))
                    with col_c:
                        st.metric("Improvements", len(result.get("weaknesses", [])))
                    with col_d:
                        st.metric("Tips", len(result.get("recommendations", [])))
                    
                    st.markdown("---")
                    
                    col_s, col_w = st.columns(2)
                    with col_s:
                        st.markdown("**✅ Strengths:**")
                        for s in result.get("strengths", []):
                            st.write(f"• {s}")
                    
                    with col_w:
                        st.markdown("**⚠️ Improvements:**")
                        for w in result.get("weaknesses", []):
                            st.write(f"• {w}")
                    
                    st.markdown("---")
                    
                    st.markdown("**💡 Recommendations:**")
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

# ═══════════════════════════════════════════════════════
# TAB 4: JOB MATCH
# ═══════════════════════════════════════════════════════

with tab4:
    st.markdown("## Find Matching Jobs")
    st.markdown("Discover opportunities that match your skills and preferences")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3, gap="large")
    
    with col1:
        st.markdown("**Your Skills:**")
        skills = st.multiselect(
            "Select skills", 
            ["Python", "JavaScript", "SQL", "Docker", "React", "FastAPI", "Go", "Java"],
            default=["Python"],
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("**Location:**")
        location = st.selectbox(
            "City",
            ["Jakarta", "Surabaya", "Bandung", "Remote"],
            label_visibility="collapsed"
        )
    
    with col3:
        st.markdown("**Target Role:**")
        role = st.selectbox(
            "Job type",
            ["Backend Dev", "Frontend Dev", "Full Stack", "Data Scientist"],
            label_visibility="collapsed"
        )
    
    if st.button("Search Jobs", use_container_width=True, key="search_jobs"):
        if skills:
            with st.spinner("Searching..."):
                result = api_client.get_recommendations(skills, location, [role])
                if "error" not in result:
                    jobs = result.get("recommendations", [])[:3]
                    
                    st.markdown(f"### Found {len(jobs)} Matching Jobs")
                    
                    for idx, job in enumerate(jobs, 1):
                        match = job.get("skill_match_percentage", 0)
                        badge = "🟢 Great Match" if match >= 80 else "🟡 Good Match" if match >= 60 else "🔴 Possible Match"
                        
                        st.markdown(f"""
                        <div class="card">
                            <div style="display: flex; justify-content: space-between; align-items: start;">
                                <div>
                                    <div style="font-size: 18px; font-weight: 700; color: #0a2540;">
                                        {job.get('job_title', 'Job Title')}
                                    </div>
                                    <div style="color: #666; font-size: 14px;">
                                        {job.get('company', 'Company')} • {job.get('location', 'Location')}
                                    </div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 24px; font-weight: bold; color: #0066cc;">
                                        {match:.0f}%
                                    </div>
                                    <div style="font-size: 12px; color: #666;">Match</div>
                                </div>
                            </div>
                            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #e5e7eb;">
                                {badge}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# TAB 5: CAREER PATH
# ═══════════════════════════════════════════════════════

with tab5:
    st.markdown("## Career Development Plan")
    st.markdown("Get personalized career guidance and growth recommendations")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        current = st.text_input("Current Role", placeholder="e.g., Junior Developer", key="current_role")
        target = st.text_input("Target Role", placeholder="e.g., Senior Developer", key="target_role")
    
    with col2:
        exp = st.number_input("Years of Experience", min_value=0, max_value=50, value=0, key="experience")
        skills = st.multiselect(
            "Your Skills",
            ["Python", "JavaScript", "SQL", "Leadership", "Communication"],
            default=["Python"],
            key="skills_career"
        )
    
    if st.button("Get Career Advice", use_container_width=True, key="career_advice"):
        if current and target and skills:
            with st.spinner("Analyzing..."):
                result = api_client.get_career_advice(current, target, skills, exp)
                if "error" not in result:
                    st.success("✅ Career plan created!")
                    
                    st.markdown(f"""
                    <div class="card">
                        <b>Goal:</b> {target}<br>
                        <b>Timeline:</b> 12-24 months<br>
                        <b>Effort Required:</b> Moderate
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

# ═══════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════

st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px 0; color: #666; font-size: 13px;">
    <p>FPP Indonesia Job Search • <a href="http://localhost:8000/docs" style="color: #0066cc; text-decoration: none;">API Docs</a> • v1.0</p>
    <p>Made with ❤️ for Indonesia Job Seekers</p>
</div>
""", unsafe_allow_html=True)
