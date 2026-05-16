import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.level_agent import level_detection_node
from agents.curriculum_agent import curriculum_planner_node
from agents.content_agent import content_generation_node
from agents.evaluator_agent import evaluator_node
from agents.progress_agent import progress_tracker_node
from langchain_core.messages import HumanMessage, AIMessage


def run_interactive_test():
    """Klavyeden girdi alarak tum 5 ajan akisini test eder."""
    print("=" * 50)
    print("VocAI Uctan Uca Test: Ajan 1 -> 2 -> 3 -> 4 -> 5")
    print("=" * 50)

    state = {
        "user_id": "",
        "session_id": "",
        "messages": [AIMessage(content="Hello! I'm your English teacher. Let's find out your English level. How are you today?")],
        "cefr_level": "",
        "assessment_complete": False,
        "daily_curriculum": None,
        "daily_content": None,
        "evaluation_result": None,
        "progress_history": None,
    }

    # ── Ajan 1: Seviye Tespiti ──────────────────────────────────────────────────
    print("\nOgretmen:", state["messages"][0].content, "\n")

    while not state["assessment_complete"]:
        user_input = input("Sen: ")
        if user_input.lower() in ["exit", "quit", "cikis"]:
            print("Test sonlandirildi.")
            return

        state["messages"].append(HumanMessage(content=user_input))
        new_state = level_detection_node(state)
        state["messages"].extend(new_state["messages"])
        state["cefr_level"] = new_state["cefr_level"]
        state["assessment_complete"] = new_state["assessment_complete"]
        print(f"\nOgretmen: {state['messages'][-1].content}\n")

    print("=" * 50)
    print(f"SEVIYE TESPIT EDILDI: {state['cefr_level']}")
    print("=" * 50)

    # ── Ajan 2: Mufredat ────────────────────────────────────────────────────────
    print("\n[Ajan 2] Mufredat hazirlaniyor...")
    state.update(curriculum_planner_node(state))
    c = state["daily_curriculum"]
    print(f"  Konu: {c['topic']} | Tema: {c['theme']}")

    # ── Ajan 3: Icerik Uretimi ──────────────────────────────────────────────────
    print("\n[Ajan 3] Ders icerigi uretiliyor...")
    state.update(content_generation_node(state))
    content = state["daily_content"]

    print("\n--- OKUMA METNI ---")
    print(content["reading_text"])

    print("\n--- KELIME LISTESI ---")
    for w in content["vocabulary_list"]:
        print(f"  {w}")

    print("\n--- DILBILGISI NOTU ---")
    print(content["grammar_note"])

    # ── Egzersiz cevaplari (Ajan 4 icin) ────────────────────────────────────────
    print("\n--- EGZERSIZLER (Cevaplarini yaz) ---")
    state["messages"] = []  # onceki mesajlari temizle, sadece cevaplar kالسين
    for i, ex in enumerate(content["exercises"], 1):
        print(f"\n{i}. [{ex['type']}] {ex['instruction']}")
        print(f"   {ex['content']}")
        answer = input("   Cevabın: ")
        state["messages"].append(HumanMessage(content=answer))

    # ── Ajan 4: Degerlendirme ───────────────────────────────────────────────────
    print("\n[Ajan 4] Cevaplar degerlendiriliyor...")
    state.update(evaluator_node(state))
    ev = state["evaluation_result"]
    print(f"\n  Skor: {ev['overall_score']:.2f}  ({ev['correct_answers']}/{ev['total_questions']} dogru)")
    print(f"  Geri bildirim: {ev['feedback']}")

    # ── Ajan 5: Ilerleme ────────────────────────────────────────────────────────
    print("\n[Ajan 5] Ilerleme kaydediliyor...")
    state.update(progress_tracker_node(state))
    summary = state["progress_history"][0]
    print(f"  Seviye: {summary['cefr_level']} | Skill deltas: {summary['skill_deltas']}")
    if summary["level_up_recommendation"]:
        print(f"  Seviye atlama onerisi: {summary['level_up_recommendation']}")

    print("\n=== UCTAN UCA TEST TAMAMLANDI ===")


def run_pipeline_test():
    """Sabit B1 state ile Ajan 2->3->4->5 akisini otomatik test eder."""
    print("\n" + "=" * 50)
    print("Pipeline Testi: Ajan 2 -> 3 -> 4 -> 5")
    print("=" * 50)

    state = {
        "user_id": "",
        "session_id": "",
        "cefr_level": "B1",
        "assessment_complete": True,
        "messages": [HumanMessage(content="I have visited Paris. Have you ever been abroad?")],
        "daily_curriculum": None,
        "daily_content": None,
        "evaluation_result": None,
        "progress_history": None,
    }

    print("\n[Ajan 2] Mufredat uretiliyor...")
    state.update(curriculum_planner_node(state))
    print(f"  Konu: {state['daily_curriculum']['topic']}")
    print(f"  Tema: {state['daily_curriculum']['theme']}")

    print("\n[Ajan 3] Icerik uretiliyor...")
    state.update(content_generation_node(state))
    content = state["daily_content"]
    print(f"  Okuma metni ({len(content['reading_text'])} karakter)")
    print(f"  {len(content['vocabulary_list'])} kelime, {len(content['exercises'])} egzersiz")

    print("\n[Ajan 4] Cevaplar degerlendiriliyor...")
    state.update(evaluator_node(state))
    ev = state["evaluation_result"]
    print(f"  Skor: {ev['overall_score']:.2f} | Geri bildirim: {ev['feedback'][:60]}...")

    print("\n[Ajan 5] Ilerleme kaydediliyor...")
    state.update(progress_tracker_node(state))
    summary = state["progress_history"][0]
    print(f"  Seviye: {summary['cefr_level']} | Skor: {summary['overall_score']}")
    if summary["level_up_recommendation"]:
        print(f"  Oneri: {summary['level_up_recommendation']}")

    print("\n=== PIPELINE TESTI TAMAMLANDI ===")


if __name__ == "__main__":
    if "--pipeline" in sys.argv:
        run_pipeline_test()
    else:
        run_interactive_test()
