import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Ajan 4 testi — cevap değerlendirme ve RAG.
Çalıştırma: python tests/test_agent4.py
"""
from langchain_core.messages import HumanMessage
from agents.evaluator_agent import evaluator_node

SAMPLE_STATE = {
    "user_id": "test_user",
    "cefr_level": "B1",
    "assessment_complete": True,
    "daily_curriculum": {
        "topic": "Present Perfect Tense",
        "theme": "Travel Experiences",
        "focus_skills": ["grammar", "vocabulary"],
        "objectives": ["Use present perfect with ever/never"],
    },
    "daily_content": {
        "reading_text": "Travel opens the mind.",
        "vocabulary_list": ["destination: a place to travel to"],
        "grammar_note": "Present perfect with ever and never for experiences.",
        "exercises": [
            {
                "type": "fill_in_blank",
                "instruction": "Complete with present perfect.",
                "content": "I _____ (visit) Paris.",
                "answer": "have visited",
            },
            {
                "type": "multiple_choice",
                "instruction": "Choose the correct option.",
                "content": "Have you _____ been to Japan? a) ever b) never",
                "answer": "a) ever",
            },
            {
                "type": "translation",
                "instruction": "Translate to English.",
                "content": "Hiç İtalya'ya gittin mi?",
                "answer": "Have you ever been to Italy?",
            },
        ],
    },
    "messages": [
        HumanMessage(content="I have visited Paris."),
        HumanMessage(content="a) ever"),
        HumanMessage(content="Have you ever been to Italy?"),
    ],
    "evaluation_result": None,
    "progress_history": None,
}

def test_evaluation():
    print("Cevaplar değerlendiriliyor...\n")
    result = evaluator_node(SAMPLE_STATE)

    assert "evaluation_result" in result
    ev = result["evaluation_result"]

    print(f"Genel skor:      {ev['overall_score']:.2f}")
    print(f"Doğru / Toplam:  {ev['correct_answers']} / {ev['total_questions']}")
    print(f"Skill deltas:    {ev['skill_deltas']}")
    print(f"RAG kaynakları:  {ev['rag_references']}")
    print(f"\nGeri bildirim:\n{ev['feedback']}")

    assert 0.0 <= ev["overall_score"] <= 1.0
    assert set(ev["skill_deltas"].keys()) >= {"grammar", "vocabulary"}
    assert ev["feedback"]
    print("\nTüm kontroller geçti.")

if __name__ == "__main__":
    test_evaluation()
