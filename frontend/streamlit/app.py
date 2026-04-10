"""
FPP Indonesia Job Search - Modern Streamlit Frontend
"""

import streamlit as st
import requests
from typing import Optional, List, Dict
import json
import time

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
                f"{self.base_url}/chat",
                json={"message": message},
                timeout=30
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
# PAGE CONFIG & STYLING
# ═══════════════════════════════════════════════════════

st.set_page_config(
    page_title="FPP Indonesia Job Search",
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
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        justify-content: center;
        background-color: white;
        border-bottom: 2px solid #e5e7eb;
        gap: 40px;
        padding: 0;
        margin: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 8px;
        background-color: white;
        border-bottom: 3px solid transparent;
        color: #4a5568;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        color: #0066cc;
        border-bottom-color: #0066cc !important;
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

api_client = APIClient("http://localhost:8000")

# ═══════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════

# Ganti HEADER section:
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 16px 40px; background: white; border-bottom: 1px solid #e5e7eb;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Crect fill='%230066cc' width='40' height='40' rx='8'/%3E%3Ctext x='50%25' y='50%25' font-size='24' font-weight='700' fill='white' text-anchor='middle' dy='.3em'%3EFPP%3C/text%3E%3C/svg%3E" style="width: 32px; height: 32px;">
        <div style="font-size: 18px; font-weight: 700; color: #0066cc;">FPP Indonesia Job Search</div>
    </div>
    <div style="font-size: 12px; color: #999;">
        Status: <span style="color: #dc2626;">● Offline</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Hilangkan header section yang lama
# col_header1, col_header2 = st.columns([1.5, 1])

# ═══════════════════════════════════════════════════════
# MAIN NAVIGATION (TABS) - CENTERED
# ═══════════════════════════════════════════════════════

if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0

if st.session_state.active_tab == 0:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Home", "💬 Chat AI", "📄 CV Analysis", "💼 Job Match", "🎯 Career Path"])
elif st.session_state.active_tab == 1:
    tab2, tab1, tab3, tab4, tab5 = st.tabs(["💬 Chat AI", "🏠 Home", "📄 CV Analysis", "💼 Job Match", "🎯 Career Path"])
elif st.session_state.active_tab == 2:
    tab3, tab1, tab2, tab4, tab5 = st.tabs(["📄 CV Analysis", "🏠 Home", "💬 Chat AI", "💼 Job Match", "🎯 Career Path"])
elif st.session_state.active_tab == 3:
    tab4, tab1, tab2, tab3, tab5 = st.tabs(["💼 Job Match", "🏠 Home", "💬 Chat AI", "📄 CV Analysis", "🎯 Career Path"])
elif st.session_state.active_tab == 4:
    tab5, tab1, tab2, tab3, tab4 = st.tabs(["🎯 Career Path", "🏠 Home", "💬 Chat AI", "📄 CV Analysis", "💼 Job Match"])

# ═══════════════════════════════════════════════════════
# TAB 1: HOME
# ═══════════════════════════════════════════════════════

with tab1:
    col1, col2 = st.columns([2, 1], gap="large")
    
    with col1:
        st.markdown("""
        <div style="padding: 20px 0;">
            <h1 style="margin: 0 0 12px 0; font-size: 48px; font-weight: 700; color: #0a2540; line-height: 1.2;">
                Smarter Job Search, Better Results
            </h1>
            <p style="margin: 0 0 24px 0; font-size: 18px; color: #666; line-height: 1.6;">
                Leverage AI to discover the right opportunities and accelerate your career
            </p>
            <div style="display: flex; gap: 12px; margin-bottom: 24px;">
                <a href="#" style="display: inline-block; background: #c8ff00; color: #0052a3; padding: 12px 28px; border-radius: 24px; font-weight: 700; text-decoration: none; transition: all 0.2s ease; font-size: 14px;">
                    Try It Now
                </a>
                <a href="#" style="display: inline-block; background: white; color: #0066cc; padding: 12px 28px; border-radius: 24px; font-weight: 700; text-decoration: none; border: 2px solid #0066cc; transition: all 0.2s ease; font-size: 14px;">
                    See How It Works
                </a>
            </div>
            <div style="background: white; border: 1px solid #e5e7eb; padding: 16px 20px; border-radius: 8px; display: inline-block; font-size: 13px; color: #666;">
                <span style="font-weight: 600; color: #0a2540;">TRUSTED BY 5,000+ JOB SEEKERS</span> • 94% Success Rate
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Quick Stats")
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("Jobs Available", "10,000+")
        with col_stat2:
            st.metric("Job Match Rate", "95%")
        with col_stat1:
            st.metric("Avg. Match Time", "2 min")
        with col_stat2:
            st.metric("Users Active", "5,000+")
    
    st.markdown("---")
    
    st.markdown("### One Stop for Your Career Journey")
    
    # Row 1
    feat_col1, feat_col2 = st.columns(2, gap="large")
    
    with feat_col1:
        st.markdown("""
        <div style="background: white; border: 1px solid #e5e7eb; padding: 24px; border-radius: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 24px; margin-bottom: 12px;">💬</div>
            <b style="color: #0a2540; display: block; font-size: 16px;">Chat AI Assistant</b>
            <p style="color: #666; font-size: 13px; margin-top: 8px; line-height: 1.5;">Ask questions about jobs, salaries, and career growth</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col2:
        st.markdown("""
        <div style="background: white; border: 1px solid #e5e7eb; padding: 24px; border-radius: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 24px; margin-bottom: 12px;">📊</div>
            <b style="color: #0a2540; display: block; font-size: 16px;">Job Tracker</b>
            <p style="color: #666; font-size: 13px; margin-top: 8px; line-height: 1.5;">Track your applications and interview progress</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Row 2
    feat_col3, feat_col4 = st.columns(2, gap="large")
    
    with feat_col3:
        st.markdown("""
        <div style="background: white; border: 1px solid #e5e7eb; padding: 24px; border-radius: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 24px; margin-bottom: 12px;">📄</div>
            <b style="color: #0a2540; display: block; font-size: 16px;">CV Analysis</b>
            <p style="color: #666; font-size: 13px; margin-top: 8px; line-height: 1.5;">Get detailed feedback on your resume and improvements</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col4:
        st.markdown("""
        <div style="background: white; border: 1px solid #e5e7eb; padding: 24px; border-radius: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 24px; margin-bottom: 12px;">💼</div>
            <b style="color: #0a2540; display: block; font-size: 16px;">Job Recommendations</b>
            <p style="color: #666; font-size: 13px; margin-top: 8px; line-height: 1.5;">Discover jobs perfectly matched to your profile</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Row 3
    feat_col5, feat_col6 = st.columns(2, gap="large")
    
    with feat_col5:
        st.markdown("""
        <div style="background: white; border: 1px solid #e5e7eb; padding: 24px; border-radius: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 24px; margin-bottom: 12px;">📝</div>
            <b style="color: #0a2540; display: block; font-size: 16px;">Resume Builder</b>
            <p style="color: #666; font-size: 13px; margin-top: 8px; line-height: 1.5;">Create professional resumes with AI assistance</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col6:
        st.markdown("""
        <div style="background: white; border: 1px solid #e5e7eb; padding: 24px; border-radius: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 24px; margin-bottom: 12px;">🎯</div>
            <b style="color: #0a2540; display: block; font-size: 16px;">Career Development</b>
            <p style="color: #666; font-size: 13px; margin-top: 8px; line-height: 1.5;">Get personalized growth path and skill recommendations</p>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# TAB 2: CHAT
# ═══════════════════════════════════════════════════════

with tab2:
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
    
    # Chat display - dengan box styling
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-end; margin: 12px 0;">
                    <div style="background: #0066cc; color: white; padding: 12px 16px; border-radius: 16px; max-width: 70%; word-wrap: break-word; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        {message['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # AI response dengan box
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-start; margin: 12px 0; gap: 12px;">
                    <div style="background: #e8eef7; border: 1px solid #d0dae8; padding: 16px; border-radius: 12px; max-width: 85%; word-wrap: break-word; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                        <div style="color: #0a2540; font-weight: 500; font-size: 14px; margin-bottom: 8px;">
                            Career Assistant
                        </div>
                        <div style="color: #333; line-height: 1.5; font-size: 14px;">
                            {message['content']}
                        </div>
                        <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #d0dae8; display: flex; gap: 16px; font-size: 12px; color: #666;">
                            <span><b>Source:</b> {message.get('source', 'General')}</span>
                            <span><b>Intent:</b> {message.get('intent', 'Unknown')}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick questions - styled seperti gambar
    st.markdown("**TRY ASKING**")
    col1, col2, col3, col4 = st.columns(4, gap="small")
    
    quick_q = [
        ("Backend jobs", "Show me backend developer jobs in Jakarta"),
        ("Salary range", "What's the average salary for senior developers?"),
        ("Skill gap", "What skills should I learn next?"),
        ("Career tips", "Give me career development advice")
    ]
    
    cols = [col1, col2, col3, col4]
    for i, (label, q) in enumerate(quick_q):
        with cols[i]:
            if st.button(label, key=f"q_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": q})
                if api_client.is_connected():
                    messages_spinner = [
                        "Searching database...",
                        "Analyzing query...",
                        "Finding matches...",
                        "Processing results...",
                        "Almost done..."
                    ]
                    
                    placeholder = st.empty()
                    resp = None
                    
                    for i in range(len(messages_spinner)):
                        with placeholder.container():
                            with st.spinner(messages_spinner[i]):
                                time.sleep(0.8)
                        if i == len(messages_spinner) - 1:
                            resp = api_client.send_message(user_id, q)
                    
                    if resp and "error" not in resp:
                        response_text = resp.get("response", "Error")
                        source = resp.get("source", "General")
                        intent = resp.get("intent", "Unknown")
                        
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": response_text,
                            "source": source,
                            "intent": intent
                        })
                        st.rerun()
    
    st.markdown("---")
    
    # Input box - styling seperti gambar
    col1, col2 = st.columns([5, 1])
    with col1:
        prompt = st.text_input("e.g., backend jobs or salary info", placeholder="Ask me anything...", label_visibility="collapsed", key="chat_input")
    with col2:
        if st.button("Send", key="send", use_container_width=True):
            if prompt:
                st.session_state.messages.append({"role": "user", "content": prompt})
                if api_client.is_connected():
                    messages_spinner = [
                        "Searching database...",
                        "Analyzing query...",
                        "Finding matches...",
                        "Processing results...",
                        "Almost done..."
                    ]
                    
                    placeholder = st.empty()
                    resp = None
                    
                    for i in range(len(messages_spinner)):
                        with placeholder.container():
                            with st.spinner(messages_spinner[i]):
                                time.sleep(0.8)
                        if i == len(messages_spinner) - 1:
                            resp = api_client.send_message(user_id, prompt)
                    
                    if resp and "error" not in resp:
                        response_text = resp.get("response", "Error")
                        source = resp.get("source", "General")
                        intent = resp.get("intent", "Unknown")
                        
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": response_text,
                            "source": source,
                            "intent": intent
                        })
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
                    
                    st.success("Analysis complete - Score: 75%")
                    
                    col_a, col_b, col_c, col_d = st.columns(4)
                    with col_a:
                        st.metric("Overall", f"{score}%")
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
                # Soft skills
                "Leadership", "Communication", "Project Management", "Agile", "Scrum",
            ],
            default=["Python"],
            label_visibility="collapsed",
            key="skills_jobmatch"
        )

    with col2:
        st.markdown("**Location:**")
        locations = st.multiselect(
            "Select cities",
            [
                "Jakarta", "Surabaya", "Bandung", "Medan", "Semarang",
                "Yogyakarta", "Bali", "Makassar", "Palembang", "Tangerang",
                "Bekasi", "Depok", "Bogor", "Malang", "Batam",
                "Remote", "Hybrid",
            ],
            default=["Jakarta"],
            label_visibility="collapsed",
            key="locations_jobmatch"
        )

    with col3:
        st.markdown("**Target Role:**")
        roles = st.multiselect(
            "Select job types",
            [
                "Backend Dev", "Frontend Dev", "Full Stack", "Mobile Dev (Android)",
                "Mobile Dev (iOS)", "Data Scientist", "Data Analyst", "Data Engineer",
                "ML Engineer", "DevOps Engineer", "Cloud Engineer", "Site Reliability Engineer",
                "QA Engineer", "Security Engineer", "Product Manager", "UI/UX Designer",
                "System Analyst", "Database Administrator", "IT Consultant",
            ],
            default=["Backend Dev"],
            label_visibility="collapsed",
            key="roles_jobmatch"
        )
    
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
        else:
            st.warning("Please select at least one skill, location, and role")

# ═══════════════════════════════════════════════════════
# TAB 5: CAREER PATH
# ═══════════════════════════════════════════════════════

with tab5:
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

# ═══════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════

st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px 0; color: #666; font-size: 13px;">
    <p>FPP Indonesia Job Search • <a href="http://localhost:8000/docs" style="color: #0066cc; text-decoration: none;">API Docs</a> • v1.0</p>
    <p>Made with care for Indonesia Job Seekers</p>
</div>
""", unsafe_allow_html=True)
