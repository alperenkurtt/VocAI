import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Oturum geçmişi CRUD testi.
Çalıştırma: python tests/test_session_history.py
"""
from database.session_history import (
    create_session, get_session, update_session_content,
    complete_session, get_user_sessions,
)
from database.client import get_collection

TEST_USER = "test_session_user_001"
SAMPLE_CURRICULUM = {
    "topic": "Present Perfect",
    "theme": "Travel experiences",
    "focus_skills": ["grammar", "speaking"],
    "objectives": ["Use have/has correctly", "Ask about experiences"],
}

def cleanup(session_id: str) -> None:
    get_collection("session_history").delete_one({"_id": session_id})

def test_session_lifecycle():
    print("1. Oturum oluşturuluyor...")
    sid = create_session(TEST_USER, "B1", SAMPLE_CURRICULUM)
    assert sid, "session_id boş olmamalı"
    print(f"   session_id: {sid}")

    print("2. Oturum getiriliyor...")
    session = get_session(sid)
    assert session is not None
    assert session["user_id"] == TEST_USER
    assert session["cefr_level"] == "B1"
    assert session["completed_at"] is None
    print(f"   started_at: {session['started_at']}")

    print("3. İçerik güncelleniyor...")
    sample_content = {"reading_text": "I have visited many countries.", "exercises": []}
    update_session_content(sid, sample_content)
    updated = get_session(sid)
    assert updated["content"]["reading_text"] == "I have visited many countries."
    print("   İçerik kaydedildi.")

    print("4. Oturum tamamlanıyor...")
    sample_eval = {"overall_score": 0.8, "feedback": "Harika iş!"}
    complete_session(sid, sample_eval)
    completed = get_session(sid)
    assert completed["completed_at"] is not None
    assert completed["evaluation"]["overall_score"] == 0.8
    print(f"   completed_at: {completed['completed_at']}")

    print("5. Kullanıcı oturumları listeleniyor...")
    sessions = get_user_sessions(TEST_USER, limit=5)
    assert len(sessions) >= 1
    print(f"   {len(sessions)} oturum bulundu.")

    cleanup(sid)
    print("\nTüm testler başarılı.")

if __name__ == "__main__":
    test_session_lifecycle()
