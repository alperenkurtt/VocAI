from datetime import datetime, timezone
from database.client import get_collection, ensure_collection

COLLECTION = "user_profiles"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _col():
    ensure_collection(COLLECTION)
    return _col()

def create_user_profile(user_id: str) -> dict:
    """Yeni kullanıcı profili oluşturur. Varsayılan beceri puanları 5/10."""
    collection = _col()
    profile = {
        "_id": user_id,
        "cefr_level": "",
        "skill_scores": {
            "grammar": 5,
            "vocabulary": 5,
            "reading": 5,
            "writing": 5,
        },
        "total_sessions": 0,
        "created_at": _now(),
        "last_active": _now(),
    }
    collection.insert_one(profile)
    return profile

def get_user_profile(user_id: str) -> dict | None:
    """Kullanıcı profilini getirir. Bulunamazsa None döner."""
    return _col().find_one({"_id": user_id})

def update_cefr_level(user_id: str, cefr_level: str) -> None:
    """Ajan 1 tamamlandıktan sonra CEFR seviyesini kaydeder."""
    _col().update_one(
        {"_id": user_id},
        {"$set": {"cefr_level": cefr_level, "last_active": _now()}},
    )

def update_skill_scores(user_id: str, skill_deltas: dict) -> None:
    """Ajan 5'in ürettiği delta değerleriyle beceri puanlarını günceller (1-10 aralığı korunur)."""
    profile = get_user_profile(user_id)
    if not profile:
        return

    current = profile.get("skill_scores", {})
    updated = {
        skill: max(1, min(10, current.get(skill, 5) + delta))
        for skill, delta in skill_deltas.items()
    }

    _col().update_one(
        {"_id": user_id},
        {"$set": {"skill_scores": {**current, **updated}, "last_active": _now()}},
    )

def increment_session_count(user_id: str) -> None:
    """Her oturum sonunda Ajan 5 tarafından çağrılır."""
    profile = get_user_profile(user_id)
    if not profile:
        return
    _col().update_one(
        {"_id": user_id},
        {"$set": {
            "total_sessions": profile.get("total_sessions", 0) + 1,
            "last_active": _now(),
        }},
    )
