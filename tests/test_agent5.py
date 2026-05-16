import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Ajan 5 testi — ilerleme takibi ve seviye atlama önerisi.
Çalıştırma: python tests/test_agent5.py
"""
from agents.progress_agent import progress_tracker_node

def make_state(score: float, user_id: str = ""):
    return {
        "user_id": user_id,
        "cefr_level": "B1",
        "session_id": "",
        "assessment_complete": True,
        "messages": [],
        "daily_curriculum": None,
        "daily_content": None,
        "evaluation_result": {
            "overall_score": score,
            "skill_deltas": {"grammar": 1, "vocabulary": 0, "reading": 0, "writing": 0},
            "feedback": "Test geri bildirimi",
            "correct_answers": 3,
            "total_questions": 3,
            "rag_references": [],
        },
        "progress_history": None,
    }

def test_low_score():
    print("1. Düşük skor senaryosu (0.5)...")
    result = progress_tracker_node(make_state(0.5))
    summary = result["progress_history"][0]
    assert summary["overall_score"] == 0.5
    assert summary["level_up_recommendation"] is None
    print(f"   Skor: {summary['overall_score']} — öneri yok. OK")

def test_high_score():
    print("2. Yüksek skor senaryosu (0.9)...")
    result = progress_tracker_node(make_state(0.9))
    summary = result["progress_history"][0]
    assert summary["overall_score"] == 0.9
    # Geçmiş oturum olmadan (user_id boş) seviye atlama önerisi gelmez
    assert summary["level_up_recommendation"] is None
    print(f"   Skor: {summary['overall_score']} — geçmiş oturum yok, öneri yok. OK")

def test_summary_fields():
    print("3. Summary alanları kontrol ediliyor...")
    result = progress_tracker_node(make_state(0.75))
    summary = result["progress_history"][0]
    assert "session_id" in summary
    assert "date" in summary
    assert "cefr_level" in summary
    assert "skill_deltas" in summary
    print("   Tüm alanlar mevcut. OK")

if __name__ == "__main__":
    test_low_score()
    test_high_score()
    test_summary_fields()
    print("\nTüm Ajan 5 testleri geçti.")
