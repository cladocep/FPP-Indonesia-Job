"""
FPP Indonesia Job Search - Streamlit Frontend Application

Fitur:
- Chat interface dengan AI assistant
- Upload dan analisis CV
- Top 3 job recommendations dengan skill match
- Skill gap analysis dengan progress bars
- Career consultation personal
- API client connector ke backend FastAPI
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
        """Cek koneksi ke API"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def send_message(self, user_id: str, message: str, session_id: Optional[str] = None) -> Dict:
        """Kirim message ke chat API"""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat/message",
                params={
                    "user_id": user_id,
                    "message": message,
                    "session_id": session_id
                },
                timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_cv(self, file_content: bytes, filename: str) -> Dict:
        """Analisis file CV"""
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
        """Dapatkan job recommendations"""
        try:
            response = requests.post(
                f"{self.base_url}/api/recommendations/personalized",
                json={
                    "current_skills": skills,
                    "desired_roles": roles or [],
                    "location": location
                },
                timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_career_advice(self, current_role: str, target_role: str, skills: List[str], experience: int) -> Dict:
        """Dapatkan career advice"""
        try:
            response = requests.post(
                f"{self.base_url}/api/consultation/career-advice",
                json={
                    "current_role": current_role,
                    "target_role": target_role,
                    "current_skills": skills,
                    "years_experience": experience
                },
                timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}


# ═══════════════════════════════════════════════════════
# STREAMLIT CONFIG
# ═══════════════════════════════════════════════════════

st.set_page_config(
    page_title="FPP Indonesia Job Search",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize API client
api_client = APIClient("http://localhost:8000")

# ═══════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════

st.sidebar.title("⚙️ Settings")
user_id = st.sidebar.text_input("User ID:", value="user_123")

# API Status indicator
api_status = "🟢 Connected" if api_client.is_connected() else "🔴 Disconnected"
st.sidebar.metric("API Status", api_status)

st.sidebar.markdown("---")
st.sidebar.markdown("**📱 Navigation**")

# ═══════════════════════════════════════════════════════
# MAIN TITLE
# ═══════════════════════════════════════════════════════

st.title("💼 FPP Indonesia Job Search AI")
st.subheader("AI Assistant untuk Pencarian Lowongan Kerja di Indonesia")

# ═══════════════════════════════════════════════════════
# PAGE NAVIGATION
# ═══════════════════════════════════════════════════════

page = st.sidebar.radio(
    "Pilih halaman:",
    ["🏠 Home", "💬 Chat", "📄 CV Analysis", "💼 Job Recommendations", "💡 Career Consultation"]
)

# ═══════════════════════════════════════════════════════
# PAGE: HOME
# ═══════════════════════════════════════════════════════

if page == "🏠 Home":
    st.markdown("""
    # Selamat Datang! 👋
    
    FPP Indonesia Job Search adalah AI-powered assistant yang membantu Anda menemukan 
    lowongan kerja yang perfect fit di Indonesia dengan analisis mendalam dan rekomendasi 
    yang dipersonalisasi berdasarkan skill dan preferensi Anda.
    
    ## ✨ Fitur Utama:
    
    ### 💬 Chat Interface
    Tanya langsung kepada AI assistant tentang lowongan kerja, info gaji, tips karir, 
    dan semua hal yang berkaitan dengan pekerjaan.
    
    ### 📄 CV Analysis
    Upload CV/Resume Anda dan dapatkan analisis lengkap tentang skill strengths, 
    weaknesses, dan rekomendasi improvement.
    
    ### 💼 Top 3 Job Recommendations
    Lihat 3 rekomendasi lowongan terbaik yang sesuai dengan skill dan preferensi Anda 
    dengan detail perusahaan, gaji, dan skill match percentage.
    
    ### 🎯 Skill Match Analysis
    Analisis detail kecocokan skill dengan setiap lowongan yang ditampilkan 
    beserta salary range dan ranking score.
    
    ### 📊 Skill Gap Progress
    Visualisasi progress skill gap dengan progress bar yang menunjukkan skill 
    mana yang perlu dikembangkan untuk mencapai target karir.
    
    ### 💡 Career Consultation
    Dapatkan konsultasi karir personal dari AI untuk pengembangan karir jangka 
    panjang dengan timeline estimasi dan actionable recommendations.
    
    ## 🚀 Mulai Sekarang:
    
    1. Pastikan API backend sudah berjalan (check status di sidebar)
    2. Pilih menu di sidebar sesuai kebutuhan Anda
    3. Ikuti instruksi di setiap halaman
    
    ---
    
    **Status:** API {status}
    """.format(status=api_status))

# ═══════════════════════════════════════════════════════
# PAGE: CHAT
# ═══════════════════════════════════════════════════════

elif page == "💬 Chat":
    st.header("💬 Chat dengan AI Assistant")
    st.markdown("Tanya apa saja tentang lowongan kerja, gaji, skill development, atau karir!")
    
    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    st.markdown("### 📝 Conversation History")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    st.markdown("---")
    
    # Chat input
    if prompt := st.chat_input("Tanya tentang lowongan, gaji, skill development, atau karir..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get and display assistant response
        with st.chat_message("assistant"):
            if api_client.is_connected():
                with st.spinner("🤔 Thinking..."):
                    response_data = api_client.send_message(user_id, prompt)
                    
                    if "error" not in response_data:
                        response = response_data.get("reply", "Maaf, terjadi kesalahan dalam memproses pertanyaan Anda")
                        st.write(response)
                        
                        # Show additional details
                        with st.expander("📊 Response Details"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Intent", response_data.get("intent", "N/A")[:20])
                            with col2:
                                st.metric("Source", response_data.get("source", "N/A"))
                            with col3:
                                confidence = response_data.get("confidence", 0)
                                st.metric("Confidence", f"{confidence*100:.0f}%")
                        
                        # Add assistant message to history
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        st.error(f"❌ Error: {response_data['error']}")
            else:
                st.warning("⚠️ API tidak terkoneksi. Silakan jalankan backend terlebih dahulu.")

# ═══════════════════════════════════════════════════════
# PAGE: CV ANALYSIS
# ═══════════════════════════════════════════════════════

elif page == "📄 CV Analysis":
    st.header("📄 Analisis CV/Resume")
    st.markdown("Upload CV Anda dan dapatkan analisis lengkap tentang kekuatan, kelemahan, dan rekomendasi improvement.")
    
    uploaded_file = st.file_uploader("Pilih file CV (PDF atau TXT):", type=["pdf", "txt"])
    
    if uploaded_file:
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"📁 **File:** `{uploaded_file.name}`")
            st.write(f"📊 **Size:** {uploaded_file.size / 1024:.2f} KB")
        
        if st.button("🔍 Analisis CV", use_container_width=True):
            with st.spinner("⏳ Menganalisis CV Anda..."):
                file_content = uploaded_file.read()
                result = api_client.analyze_cv(file_content, uploaded_file.name)
                
                if "error" not in result:
                    st.success("✅ Analisis selesai!")
                    
                    # Overall Score
                    st.markdown("### 📊 Skor Keseluruhan")
                    overall_score = result.get("overall_score", 0)
                    st.progress(overall_score / 100, f"**Score:** {overall_score:.1f}%")
                    
                    # Strengths and Weaknesses
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### ✅ Kekuatan CV Anda")
                        strengths = result.get("strengths", [])
                        if strengths:
                            for strength in strengths:
                                st.success(strength)
                        else:
                            st.info("Tidak ada data kekuatan")
                    
                    with col2:
                        st.markdown("### ⚠️ Area Improvement")
                        weaknesses = result.get("weaknesses", [])
                        if weaknesses:
                            for weakness in weaknesses:
                                st.warning(weakness)
                        else:
                            st.info("CV Anda sudah bagus!")
                    
                    # Recommendations
                    st.markdown("### 💡 Rekomendasi Perbaikan")
                    recommendations = result.get("recommendations", [])
                    if recommendations:
                        for i, rec in enumerate(recommendations, 1):
                            st.info(f"**{i}.** {rec}")
                    else:
                        st.info("Tidak ada rekomendasi khusus")
                else:
                    st.error(f"❌ Error: {result['error']}")

# ═══════════════════════════════════════════════════════
# PAGE: JOB RECOMMENDATIONS
# ═══════════════════════════════════════════════════════

elif page == "💼 Job Recommendations":
    st.header("💼 Top 3 Rekomendasi Pekerjaan")
    st.markdown("Masukkan preferensi Anda dan dapatkan 3 rekomendasi lowongan terbaik dengan skill match analysis.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🔧 Skill Anda")
        skills = st.multiselect(
            "Pilih skill yang Anda kuasai:",
            ["Python", "JavaScript", "TypeScript", "SQL", "Docker", "Kubernetes", "React", 
             "Vue.js", "Angular", "FastAPI", "Django", "Node.js", "Go", "Rust", "Java",
             "Data Science", "Machine Learning", "Deep Learning", "AWS", "GCP", "Azure",
             "Git", "Linux", "Jenkins", "CI/CD", "Communication", "Leadership"],
            default=["Python", "FastAPI"],
            key="skills_rec"
        )
        
        st.markdown("#### 📍 Lokasi Kerja")
        location = st.selectbox(
            "Lokasi preferensi:",
            ["Jakarta", "Surabaya", "Bandung", "Medan", "Yogyakarta", "Semarang", "Remote", "Hybrid"],
            key="location_rec"
        )
    
    with col2:
        st.markdown("#### 💼 Posisi Target")
        roles = st.multiselect(
            "Posisi yang Anda inginkan:",
            ["Data Scientist", "Backend Developer", "Frontend Developer", "Full Stack Developer",
             "ML Engineer", "DevOps Engineer", "Cloud Architect", "Data Analyst", "QA Engineer", 
             "Product Manager", "Tech Lead", "Software Architect"],
            default=["Backend Developer"],
            key="roles_rec"
        )
    
    if st.button("🔍 Cari Rekomendasi", use_container_width=True):
        if skills and location:
            with st.spinner("⏳ Mencari rekomendasi terbaik untuk Anda..."):
                result = api_client.get_recommendations(skills, location, roles)
                
                if "error" not in result:
                    st.success("✅ Rekomendasi ditemukan!")
                    st.markdown("### 🏆 Top 3 Rekomendasi Lowongan")
                    
                    recommendations = result.get("recommendations", [])[:3]
                    for idx, job in enumerate(recommendations, 1):
                        with st.container():
                            col1, col2, col3 = st.columns([2, 1.5, 1])
                            
                            with col1:
                                st.markdown(f"### #{idx} {job.get('job_title', 'N/A')}")
                                st.write(f"**🏢 Perusahaan:** {job.get('company', 'N/A')}")
                                st.write(f"**📍 Lokasi:** {job.get('location', 'N/A')}")
                                st.write(f"**💰 Gaji:** Rp {job.get('salary_min', 0):,} - Rp {job.get('salary_max', 0):,}/bulan")
                            
                            with col2:
                                st.markdown("**🎯 Skill Match**")
                                skill_match = job.get('skill_match_percentage', 0)
                                st.progress(skill_match / 100, f"{skill_match:.0f}%")
                            
                            with col3:
                                st.markdown("**⭐ Score**")
                                st.metric("", f"{job.get('match_score', 0):.1f}/100")
                            
                            st.markdown("---")
                else:
                    st.error(f"❌ Error: {result['error']}")
        else:
            st.warning("⚠️ Silakan pilih minimal 1 skill dan 1 lokasi")

# ═══════════════════════════════════════════════════════
# PAGE: CAREER CONSULTATION
# ═══════════════════════════════════════════════════════

elif page == "💡 Career Consultation":
    st.header("💡 Konsultasi Karir Personal")
    st.markdown("Dapatkan saran pengembangan karir yang dipersonalisasi dari AI assistant berdasarkan data dan skill Anda.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 💼 Posisi Saat Ini")
        current_role = st.text_input(
            "Posisi Anda sekarang:",
            placeholder="misal: Junior Backend Developer",
            key="current_role_cons"
        )
        
        st.markdown("#### 📈 Pengalaman Kerja")
        years_exp = st.number_input(
            "Berapa tahun pengalaman kerja?",
            min_value=0,
            max_value=50,
            value=0,
            key="years_exp_cons"
        )
    
    with col2:
        st.markdown("#### 🎯 Target Karir")
        target_role = st.text_input(
            "Target posisi (5 tahun ke depan):",
            placeholder="misal: Senior Backend Developer",
            key="target_role_cons"
        )
    
    st.markdown("#### 🔧 Skill Saat Ini")
    skills_cons = st.multiselect(
        "Pilih skill yang sudah Anda kuasai:",
        ["Python", "JavaScript", "TypeScript", "SQL", "Docker", "Kubernetes", "React",
         "Vue.js", "Angular", "FastAPI", "Django", "Node.js", "Go", "Rust", "Java",
         "Data Science", "Machine Learning", "AWS", "GCP", "Leadership", "Communication"],
        default=["Python"],
        key="skills_cons"
    )
    
    if st.button("📚 Dapatkan Saran Karir", use_container_width=True):
        if current_role and target_role and skills_cons:
            with st.spinner("⏳ Menganalisis path karir Anda..."):
                result = api_client.get_career_advice(current_role, target_role, skills_cons, years_exp)
                
                if "error" not in result:
                    st.success("✅ Analisis selesai!")
                    
                    st.markdown("### 🎯 Saran Pengembangan Karir")
                    st.write(result.get("career_advice", ""))
                    
                    st.markdown("### 📚 Skill yang Perlu Dikembangkan")
                    recommendations = result.get("recommendations", [])[:5]
                    if recommendations:
                        for skill_rec in recommendations:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"• {skill_rec}")
                            with col2:
                                st.progress(0.65, "65%")
                    
                    st.markdown("### 📊 Progress Skill Development")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📌 Skill Owned", len(skills_cons))
                    with col2:
                        st.metric("📝 Skills to Learn", len(recommendations))
                    with col3:
                        total_skills = len(skills_cons) + len(recommendations)
                        progress_pct = (len(skills_cons) / total_skills * 100) if total_skills > 0 else 0
                        st.metric("📈 Progress", f"{progress_pct:.0f}%")
                    
                    st.markdown("### ⏱️ Timeline Estimasi")
                    st.info(
                        "📅 **Estimated Timeline:** 12-24 bulan untuk mencapai target posisi dengan dedikasi "
                        "dan fokus pada skill development yang direkomendasikan."
                    )
                else:
                    st.error(f"❌ Error: {result['error']}")
        else:
            st.warning("⚠️ Silakan lengkapi semua field")

# ═══════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════

st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🔗 Quick Links**")
    st.markdown("- [API Docs](http://localhost:8000/docs)")
    st.markdown("- [GitHub](https://github.com)")

with col2:
    st.markdown("**📧 Support**")
    st.markdown("- Contact: support@fpp.id")
    st.markdown("- Status: Active")

with col3:
    st.markdown("**📊 Version Info**")
    st.markdown("- Version: v1.0.0")
    st.markdown("- Framework: Streamlit")

st.markdown("---")
st.markdown(
    "Made with ❤️ for FPP Indonesia Job Search | Powered by OpenAI, FastAPI & Streamlit"
)
