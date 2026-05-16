import streamlit as st

st.set_page_config(page_title="Günlük Ders — VocAI", page_icon="📖", layout="centered")

if not st.session_state.get("user_id"):
    st.warning("Önce ana sayfadan giriş yap.")
    st.page_link("app.py", label="Ana Sayfaya Git")
    st.stop()

if not st.session_state.get("assessment_complete"):
    st.warning("Önce seviye testini tamamla.")
    st.page_link("pages/1_Assessment.py", label="Seviye Testine Git", icon="🎯")
    st.stop()

curriculum = st.session_state.get("daily_curriculum")
content = st.session_state.get("daily_content")

st.title("📖 Günlük Ders")

# ── Ders başlığı ────────────────────────────────────────────────────────────────
if curriculum:
    st.markdown(f"## {curriculum['topic']}")
    st.caption(f"Tema: {curriculum['theme']}  •  Seviye: {st.session_state.cefr_level}")

    focus = " • ".join(s.capitalize() for s in curriculum.get("focus_skills", []))
    st.markdown(f"**Odak Becerileri:** {focus}")

    with st.expander("Hedefler"):
        for obj in curriculum.get("objectives", []):
            st.markdown(f"- {obj}")

st.markdown("---")

if not content:
    st.info("İçerik henüz hazır değil. Seviye testini tamamla.")
    st.stop()

# ── Okuma Metni ─────────────────────────────────────────────────────────────────
st.subheader("📄 Okuma Metni")
st.markdown(content["reading_text"])

st.markdown("---")

# ── Kelime Listesi ──────────────────────────────────────────────────────────────
st.subheader("📝 Kelime Listesi")
cols = st.columns(2)
for i, word in enumerate(content["vocabulary_list"]):
    with cols[i % 2]:
        if ":" in word:
            term, definition = word.split(":", 1)
            st.markdown(f"**{term.strip()}** — {definition.strip()}")
        else:
            st.markdown(f"• {word}")

st.markdown("---")

# ── Dilbilgisi Notu ─────────────────────────────────────────────────────────────
st.subheader("💡 Dilbilgisi Notu")
st.info(content["grammar_note"])

st.markdown("---")

# ── Pratik Yap butonu ───────────────────────────────────────────────────────────
st.subheader("✏️ Hazır mısın?")
st.markdown(f"Bu derste **{len(content['exercises'])} egzersiz** seni bekliyor.")
st.page_link("pages/4_Practice.py", label="Pratik Yapmaya Başla →", icon="✏️")
