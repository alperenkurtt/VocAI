import streamlit as st

st.set_page_config(
    page_title="VocAI",
    page_icon="📚",
    layout="centered",
)

# ── Session state başlatma ──────────────────────────────────────────────────────
def init_state():
    defaults = {
        "user_id": "",
        "session_id": "",
        "cefr_level": "",
        "assessment_complete": False,
        "daily_curriculum": None,
        "daily_content": None,
        "evaluation_result": None,
        "progress_history": None,
        "messages": [],       # BaseMessage listesi (Ajan 1 için)
        "exercise_answers": [],  # Kullanıcının egzersiz cevapları
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_state()

# ── Kullanıcı girişi ────────────────────────────────────────────────────────────
st.title("📚 VocAI")
st.markdown("**İngilizce öğrenme asistanın — CEFR seviyene göre kişiselleştirilmiş dersler.**")

if not st.session_state.user_id:
    st.markdown("---")
    st.subheader("Başlamak için kullanıcı adı gir")
    with st.form("login_form"):
        username = st.text_input("Kullanıcı adı", placeholder="örn: alperen")
        submitted = st.form_submit_button("Giriş Yap")

    if submitted and username.strip():
        st.session_state.user_id = username.strip().lower()

        # Kullanıcı profilini oluştur ya da getir
        from database.user_profiles import get_user_profile, create_user_profile
        profile = get_user_profile(st.session_state.user_id)
        if not profile:
            create_user_profile(st.session_state.user_id)

        st.rerun()
else:
    st.success(f"Hoş geldin, **{st.session_state.user_id}**!")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.page_link("pages/1_Assessment.py", label="Seviye Testi", icon="🎯")
    with col2:
        st.page_link("pages/2_Dashboard.py", label="Profilim", icon="📊")
    with col3:
        st.page_link("pages/3_Daily_Lesson.py", label="Günlük Ders", icon="📖")
    with col4:
        st.page_link("pages/4_Practice.py", label="Pratik Yap", icon="✏️")

    st.markdown("---")

    # Durum özeti
    if st.session_state.cefr_level:
        st.info(f"Seviyeniz: **{st.session_state.cefr_level}**")
    else:
        st.warning("Henüz seviye testi yapılmadı. **Seviye Testi** sayfasına git.")

    if st.button("Çıkış Yap / Kullanıcı Değiştir"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
