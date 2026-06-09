"""
Seviye atlama senaryosu için test kullanıcısı oluşturur ve siler.

Kullanım:
    python -m tests.seed_levelup_user              # interaktif mod
    python -m tests.seed_levelup_user create       # kullanıcı oluştur
    python -m tests.seed_levelup_user delete       # kullanıcı sil
"""

import uuid
import sys
from datetime import datetime, timezone, timedelta
from database.client import get_collection, ensure_collection
from database import user_profiles, session_history
from agents.progress_agent import LEVEL_UP_THRESHOLDS, _DEFAULT_THRESHOLD


def _col_profiles():
    ensure_collection("user_profiles")
    return get_collection("user_profiles")

def _col_sessions():
    ensure_collection("session_history")
    return get_collection("session_history")

def _now_minus(days: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return dt.isoformat()


def create_near_levelup_user(username: str, cefr_level: str) -> dict:
    """
    Verilen kullanıcı adı ve CEFR seviyesiyle, seviye atlamasına
    tam 1 pratik kalmış bir kullanıcı oluşturur.

    Durum:
      - level_up_candidate = True  (aday belirlendi)
      - confirmation_sessions_passed = 1  (2 gerekli, 1 tamamlandı)
      - skill_scores tüm becerilerde skill_min + 5 (eşiğin üzerinde)
      - min_sessions + 2 adet tamamlanmış oturum mevcut
    """
    thresholds   = LEVEL_UP_THRESHOLDS.get(cefr_level, _DEFAULT_THRESHOLD)
    skill_min    = thresholds["skill_min"]
    min_sessions = thresholds["min_sessions"]
    avg_score    = thresholds["avg_score"]

    # 1. Kullanıcı profili oluştur
    user_id = str(uuid.uuid4())
    user_profiles.create_user_profile(user_id, username, "test1234")

    # 2. Seviye ve skill skorlarını doğrudan yaz
    target_skill = skill_min + 5
    _col_profiles().update_one(
        {"_id": user_id},
        {"$set": {
            "cefr_level": cefr_level,
            "skill_scores": {
                "grammar":    target_skill,
                "vocabulary": target_skill,
                "reading":    target_skill,
                "writing":    target_skill,
            },
            "total_sessions":             min_sessions + 2,
            "sessions_at_current_level":  min_sessions + 2,
            "level_up_candidate":         True,
            "confirmation_sessions_passed": 1,
            # Son 5 oturumun readiness ortalaması eşiğin üzerinde
            "readiness_scores": [thresholds["readiness_min"] + 0.05] * 5,
            "skill_trend": {
                "grammar":    [1] * 10,
                "vocabulary": [1] * 10,
                "reading":    [1] * 10,
                "writing":    [1] * 10,
            },
        }},
    )

    # 3. Oturum geçmişi oluştur
    session_count = min_sessions + 2
    for i in range(session_count):
        sid = str(uuid.uuid4())
        started_at = _now_minus(session_count - i)
        curriculum = {"topic": "English grammar", "objectives": ["Practice B1 structures"]}
        content    = {"exercises": [], "reading_text": ""}
        evaluation = {
            "overall_score":        round(avg_score + 0.03, 2),
            "skill_deltas":         {"grammar": 1, "vocabulary": 1, "reading": 1, "writing": 1},
            "feedback":             "Good performance.",
            "correct_answers":      4,
            "total_questions":      5,
            "rag_references":       [],
            "next_level_readiness": round(thresholds["readiness_min"] + 0.05, 2),
            "structural_complexity": 3,
        }
        _col_sessions().insert_one({
            "_id":          sid,
            "user_id":      user_id,
            "cefr_level":   cefr_level,
            "curriculum":   curriculum,
            "content":      content,
            "evaluation":   evaluation,
            "started_at":   started_at,
            "completed_at": started_at,
        })

    from agents.progress_agent import LEVEL_ORDER
    next_level = LEVEL_ORDER[LEVEL_ORDER.index(cefr_level) + 1] if cefr_level in LEVEL_ORDER else "?"

    print(f"\nKullanıcı oluşturuldu:")
    print(f"  Kullanıcı adı : {username}")
    print(f"  Şifre         : test1234")
    print(f"  user_id       : {user_id}")
    print(f"  Mevcut seviye : {cefr_level}")
    print(f"  Hedef seviye  : {next_level}")
    print(f"  Skill skorlar : {target_skill}/100 (tüm beceriler)")
    print(f"  Oturum sayısı : {session_count}")
    print(f"  Aday durumu   : True (1/2 onay tamamlandı)")
    print(f"\n  --> Bir sonraki pratik oturumunda seviye {cefr_level} → {next_level} atlayacak.\n")

    return {"user_id": user_id, "username": username, "cefr_level": cefr_level, "password": "test1234"}


def delete_test_user(username: str) -> bool:
    """
    Kullanıcı adına göre kullanıcıyı ve tüm oturum geçmişini siler.
    Başarılıysa True, bulunamazsa False döner.
    """
    profile = user_profiles.find_by_username(username)
    if not profile:
        print(f"Kullanıcı bulunamadı: {username}")
        return False

    user_id = profile["_id"]

    # Oturum geçmişini sil
    sessions = _col_sessions().find({"user_id": user_id})
    deleted_sessions = 0
    for s in sessions:
        _col_sessions().delete_one({"_id": s["_id"]})
        deleted_sessions += 1

    # Profili sil
    user_profiles.delete_user(user_id)

    print(f"\nSilindi:")
    print(f"  Kullanıcı : {username} ({user_id})")
    print(f"  Oturumlar : {deleted_sessions} adet\n")
    return True


def _interactive():
    print("=== Seviye Atlama Test Kullanıcısı ===\n")
    print("1) Kullanıcı oluştur")
    print("2) Kullanıcı sil")
    choice = input("\nSeçim (1/2): ").strip()

    if choice == "1":
        username   = input("Kullanıcı adı: ").strip()
        cefr_level = input("CEFR seviyesi (A1/A2/B1/B2/C1): ").strip().upper()
        valid = ["A1", "A2", "B1", "B2", "C1"]
        if cefr_level not in valid:
            print(f"Geçersiz seviye. Seçenekler: {valid}")
            return
        create_near_levelup_user(username, cefr_level)

    elif choice == "2":
        username = input("Silinecek kullanıcı adı: ").strip()
        delete_test_user(username)

    else:
        print("Geçersiz seçim.")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        _interactive()

    elif args[0] == "create":
        username   = input("Kullanıcı adı: ").strip()
        cefr_level = input("CEFR seviyesi (A1/A2/B1/B2/C1): ").strip().upper()
        create_near_levelup_user(username, cefr_level)

    elif args[0] == "delete":
        username = input("Silinecek kullanıcı adı: ").strip()
        delete_test_user(username)
