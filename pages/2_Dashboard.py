import streamlit as st

st.set_page_config(page_title="Profilim — VocAI", page_icon="📊", layout="centered")

if not st.session_state.get("user_id"):
    st.warning("Önce ana sayfadan giriş yap.")
    st.page_link("app.py", label="Ana Sayfaya Git")
    st.stop()

from database.user_profiles import get_user_profile

st.title("📊 Profilim")

profile = get_user_profile(st.session_state.user_id)

if not profile:
    st.error("Profil bulunamadı.")
    st.stop()

# ── Genel bilgiler ──────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Seviye", profile.get("cefr_level") or "—")
with col2:
    st.metric("Toplam Oturum", profile.get("total_sessions", 0))
with col3:
    last = profile.get("last_active", "")[:10] if profile.get("last_active") else "—"
    st.metric("Son Aktif", last)

st.markdown("---")

# ── Beceri skorları ─────────────────────────────────────────────────────────────
st.subheader("Beceri Skorları")
skills = profile.get("skill_scores", {})

if skills:
    import pandas as pd
    df = pd.DataFrame({
        "Beceri": [k.capitalize() for k in skills],
        "Puan": list(skills.values()),
    })
    st.bar_chart(df.set_index("Beceri"), y="Puan", y_label="Puan (1-10)", x_label="Beceri")

    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]
    for i, (skill, score) in enumerate(skills.items()):
        with cols[i]:
            st.metric(skill.capitalize(), f"{score}/10")
else:
    st.info("Henüz beceri skoru yok. Pratik yaptıkça güncellenir.")

st.markdown("---")

# ── Son oturum ──────────────────────────────────────────────────────────────────
if st.session_state.get("progress_history"):
    st.subheader("Son Oturum Özeti")
    summary = st.session_state.progress_history[0]
    st.write(f"Skor: **{summary['overall_score']:.0%}**")
    if summary.get("level_up_recommendation"):
        st.success(f"Seviye atlama önerisi: {summary['level_up_recommendation']}")
    deltas = summary.get("skill_deltas", {})
    if deltas:
        d_col = st.columns(len(deltas))
        for i, (skill, delta) in enumerate(deltas.items()):
            sign = "+" if delta > 0 else ""
            d_col[i].metric(skill.capitalize(), f"{sign}{delta}")
else:
    st.info("Henüz tamamlanan oturum yok.")
