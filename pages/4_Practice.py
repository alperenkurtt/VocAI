import streamlit as st
from langchain_core.messages import HumanMessage

st.set_page_config(page_title="Pratik — VocAI", page_icon="✏️", layout="centered")

if not st.session_state.get("user_id"):
    st.warning("Önce ana sayfadan giriş yap.")
    st.page_link("app.py", label="Ana Sayfaya Git")
    st.stop()

if not st.session_state.get("daily_content"):
    st.warning("Önce günlük dersi tamamla.")
    st.page_link("pages/3_Daily_Lesson.py", label="Günlük Derse Git", icon="📖")
    st.stop()

from agents.evaluator_agent import evaluator_node
from agents.progress_agent import progress_tracker_node

st.title("✏️ Pratik Yap")

content = st.session_state.daily_content
exercises = content.get("exercises", [])

# ── Değerlendirme tamamlandıysa sonuçları göster ────────────────────────────────
if st.session_state.get("evaluation_result"):
    ev = st.session_state.evaluation_result
    summary = (st.session_state.progress_history or [{}])[0]

    st.success("Tebrikler, dersi tamamladın!")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Genel Skor", f"{ev['overall_score']:.0%}")
    with col2:
        st.metric("Doğru / Toplam", f"{ev['correct_answers']} / {ev['total_questions']}")

    st.markdown("---")
    st.subheader("Geri Bildirim")
    st.info(ev["feedback"])

    st.markdown("---")
    st.subheader("Beceri Değişimleri")
    deltas = ev.get("skill_deltas", {})
    d_cols = st.columns(len(deltas))
    for i, (skill, delta) in enumerate(deltas.items()):
        sign = "+" if delta > 0 else ""
        d_cols[i].metric(skill.capitalize(), f"{sign}{delta}", delta_color="normal")

    if summary.get("level_up_recommendation"):
        st.success(f"Seviye atlama önerisi: **{summary['level_up_recommendation']}**")

    st.markdown("---")
    if st.button("Yeni Ders Başlat"):
        st.session_state.daily_curriculum = None
        st.session_state.daily_content = None
        st.session_state.evaluation_result = None
        st.session_state.progress_history = None
        st.session_state.exercise_answers = []
        st.session_state.assessment_complete = False
        st.session_state.messages = []
        st.rerun()
    st.stop()

# ── Egzersizler formu ───────────────────────────────────────────────────────────
TYPE_LABELS = {
    "fill_in_blank": "Boşluk Doldur",
    "multiple_choice": "Çoktan Seçmeli",
    "translation": "Çeviri",
    "writing_prompt": "Yazma",
}

with st.form("exercises_form"):
    answers = []
    for i, ex in enumerate(exercises, 1):
        label = TYPE_LABELS.get(ex["type"], ex["type"])
        st.markdown(f"### Egzersiz {i} — {label}")
        st.markdown(f"**{ex['instruction']}**")
        st.markdown(ex["content"])
        ans = st.text_area(f"Cevabın:", key=f"ex_{i}", height=80)
        answers.append(ans)
        st.markdown("---")

    submitted = st.form_submit_button("Cevapları Gönder", type="primary")

if submitted:
    if not any(a.strip() for a in answers):
        st.error("En az bir egzersizi cevapla.")
    else:
        with st.spinner("Cevapların değerlendiriliyor..."):
            # Cevapları HumanMessage listesine çevir
            answer_messages = [HumanMessage(content=a or "(boş)") for a in answers]

            state = {
                "user_id": st.session_state.user_id,
                "session_id": st.session_state.session_id,
                "cefr_level": st.session_state.cefr_level,
                "daily_content": st.session_state.daily_content,
                "messages": answer_messages,
                "evaluation_result": None,
                "progress_history": None,
            }

            # Ajan 4: Değerlendirme
            eval_result = evaluator_node(state)
            st.session_state.evaluation_result = eval_result["evaluation_result"]

            # Ajan 5: İlerleme (skill skorlarını ve session'ı DB'ye yazar)
            state["evaluation_result"] = st.session_state.evaluation_result
            progress_result = progress_tracker_node(state)
            st.session_state.progress_history = progress_result["progress_history"]

        st.rerun()
