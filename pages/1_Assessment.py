import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(page_title="Seviye Testi — VocAI", page_icon="🎯", layout="centered")

if not st.session_state.get("user_id"):
    st.warning("Önce ana sayfadan giriş yap.")
    st.page_link("app.py", label="Ana Sayfaya Git")
    st.stop()

from agents.level_agent import level_detection_node
from agents.curriculum_agent import curriculum_planner_node
from agents.content_agent import content_generation_node
from database.session_history import create_session
from database.user_profiles import update_cefr_level

st.title("🎯 Seviye Testi")

# İlk mesajı başlat
if not st.session_state.get("messages"):
    st.session_state.messages = [AIMessage(content=(
        "Merhaba! Ben VocAI, İngilizce öğrenme asistanınım. "
        "Sana birkaç soru sorarak İngilizce seviyeni tespit edeceğim.\n\n"
        "Hello! Let's start. How are you today? Tell me a little about yourself."
    ))]

# ── Tamamlandıysa: ders hazırla ve yönlendir ─────────────────────────────────
if st.session_state.get("assessment_complete"):
    st.success(f"Seviye tespiti tamamlandı! Seviyeniz: **{st.session_state.cefr_level}**")

    # Müfredat/içerik hâlâ yoksa burada üret (sayfa yenileme, tarayıcı geri dönüşü gibi durumlarda)
    if not st.session_state.get("daily_curriculum"):
        with st.spinner("Müfredat hazırlanıyor..."):
            try:
                result = curriculum_planner_node({"cefr_level": st.session_state.cefr_level, "daily_curriculum": None})
                st.session_state.daily_curriculum = result["daily_curriculum"]
            except Exception as e:
                st.error(f"Müfredat üretilemedi: {e}")

    if st.session_state.get("daily_curriculum") and not st.session_state.get("daily_content"):
        with st.spinner("Ders içeriği hazırlanıyor..."):
            try:
                result = content_generation_node({
                    "cefr_level": st.session_state.cefr_level,
                    "daily_curriculum": st.session_state.daily_curriculum,
                })
                st.session_state.daily_content = result["daily_content"]
            except Exception as e:
                st.error(f"Ders içeriği üretilemedi: {e}")

    if st.session_state.get("daily_curriculum"):
        c = st.session_state.daily_curriculum
        st.info(f"Bugünkü ders: **{c['topic']}** — {c['theme']}")

    col1, col2 = st.columns(2)
    with col1:
        st.page_link("pages/3_Daily_Lesson.py", label="Günlük Derse Git", icon="📖")
    with col2:
        if st.button("Testi Yeniden Başlat"):
            st.session_state.messages = []
            st.session_state.cefr_level = ""
            st.session_state.assessment_complete = False
            st.session_state.daily_curriculum = None
            st.session_state.daily_content = None
            st.session_state.evaluation_result = None
            st.session_state.progress_history = None
            st.session_state.session_id = ""
            st.session_state.exercise_answers = []
            st.rerun()

    st.markdown("---")

# ── Mesaj geçmişini göster ───────────────────────────────────────────────────
for msg in st.session_state.get("messages", []):
    role = "assistant" if isinstance(msg, AIMessage) else "user"
    with st.chat_message(role):
        st.write(msg.content)

# ── Kullanıcı girişi ─────────────────────────────────────────────────────────
if not st.session_state.get("assessment_complete"):
    if user_input := st.chat_input("Cevabınızı yazın..."):
        # Kullanıcı mesajını ekle ve göster
        st.session_state.messages.append(HumanMessage(content=user_input))
        with st.chat_message("user"):
            st.write(user_input)

        # Ajan 1
        with st.chat_message("assistant"):
            with st.spinner("Düşünüyor..."):
                try:
                    result = level_detection_node({
                        "messages": st.session_state.messages,
                        "cefr_level": st.session_state.get("cefr_level", ""),
                        "assessment_complete": False,
                    })
                except Exception as e:
                    st.error(f"Ajan 1 hatası: {e}")
                    st.stop()

            new_msg = result["messages"][-1]
            st.write(new_msg.content)

        st.session_state.messages.append(new_msg)
        st.session_state.cefr_level = result["cefr_level"]
        st.session_state.assessment_complete = result["assessment_complete"]

        # Seviye belirlendiyse Ajan 2 + 3 çalıştır
        if result["assessment_complete"]:
            with st.spinner("Müfredat hazırlanıyor..."):
                try:
                    r2 = curriculum_planner_node({
                        "cefr_level": st.session_state.cefr_level,
                        "daily_curriculum": None,
                    })
                    st.session_state.daily_curriculum = r2["daily_curriculum"]
                except Exception as e:
                    st.error(f"Müfredat üretilemedi: {e}")

            with st.spinner("Ders içeriği hazırlanıyor..."):
                try:
                    r3 = content_generation_node({
                        "cefr_level": st.session_state.cefr_level,
                        "daily_curriculum": st.session_state.daily_curriculum,
                    })
                    st.session_state.daily_content = r3["daily_content"]
                except Exception as e:
                    st.error(f"İçerik üretilemedi: {e}")

            # CEFR seviyesini DB'ye kaydet
            try:
                update_cefr_level(st.session_state.user_id, st.session_state.cefr_level)
            except Exception as e:
                st.warning(f"Seviye kaydedilemedi: {e}")

            # Oturum kaydı
            try:
                sid = create_session(
                    st.session_state.user_id,
                    st.session_state.cefr_level,
                    st.session_state.daily_curriculum or {},
                )
                st.session_state.session_id = sid
            except Exception as e:
                st.warning(f"Oturum kaydedilemedi: {e}")

        st.rerun()
