import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Ajan 3 testi — B1 seviyesi için içerik üretimi.
Çalıştırma: python tests/test_agent3.py
"""
import json
from agents.content_agent import content_generation_node

SAMPLE_STATE = {
    "user_id": "test_user",
    "cefr_level": "B1",
    "daily_curriculum": {
        "topic": "Present Perfect Tense",
        "theme": "Travel Experiences",
        "focus_skills": ["grammar", "vocabulary", "reading"],
        "objectives": [
            "Use present perfect correctly with 'ever' and 'never'",
            "Learn 8 travel-related vocabulary words",
        ],
    },
    "messages": [],
    "assessment_complete": True,
    "daily_content": None,
    "evaluation_result": None,
    "progress_history": None,
}

def test_content_generation():
    print("B1 seviyesi için içerik üretiliyor...\n")
    result = content_generation_node(SAMPLE_STATE)

    assert "daily_content" in result
    content = result["daily_content"]

    print("=== OKUMA METNİ ===")
    print(content["reading_text"])

    print("\n=== KELİME LİSTESİ ===")
    for word in content["vocabulary_list"]:
        print(f"  - {word}")

    print("\n=== DİLBİLGİSİ NOTU ===")
    print(content["grammar_note"])

    print("\n=== EGZERSİZLER ===")
    for i, ex in enumerate(content["exercises"], 1):
        print(f"\n{i}. [{ex['type']}] {ex['instruction']}")
        print(f"   {ex['content']}")
        if ex.get("answer"):
            print(f"   Cevap: {ex['answer']}")

    # Doğrulamalar
    assert content["reading_text"], "reading_text boş olamaz"
    assert len(content["vocabulary_list"]) >= 5, "En az 5 kelime olmalı"
    assert len(content["exercises"]) >= 3, "En az 3 egzersiz olmalı"
    assert content["grammar_note"], "grammar_note boş olamaz"

    print("\nTüm kontroller geçti.")

if __name__ == "__main__":
    test_content_generation()
