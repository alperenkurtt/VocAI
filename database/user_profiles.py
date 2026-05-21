import bcrypt
from datetime import datetime, timezone
from database.client import get_collection, ensure_collection

COLLECTION = "user_profiles"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _col():
    ensure_collection(COLLECTION)
    return get_collection(COLLECTION)

def _hash_password(password: str) -> str:
    """Şifreyi bcrypt ile hashler."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def _verify_password(password: str, hashed: str) -> bool:
    """Şifreyi doğrular."""
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_user_profile(user_id: str, username: str, password: str) -> dict:
    """Yeni kullanıcı profili oluşturur. Şifre bcrypt ile hashlenir."""
    profile = {
        "_id": user_id,
        "username": username,
        "password_hash": _hash_password(password),
        "cefr_level": "",
        # Beceri puanları 0-100 skalasında, başlangıç 50
        "skill_scores": {
            "grammar": 50,
            "vocabulary": 50,
            "reading": 50,
            "writing": 50,
        },
        "total_sessions": 0,
        "created_at": _now(),
        "last_active": _now(),
    }
    _col().insert_one(profile)
    return profile

def find_by_username(username: str) -> dict | None:
    """Kullanıcı adına göre profil arar."""
    return _col().find_one({"username": username})

def verify_login(username: str, password: str) -> dict | None:
    """Kullanıcı adı ve şifre doğruysa profili döner, değilse None."""
    profile = find_by_username(username)
    if not profile:
        return None
    hashed = profile.get("password_hash", "")
    if not hashed:
        # Şifresi olmayan eski kullanıcılar için (migration)
        return None
    if _verify_password(password, hashed):
        return profile
    return None

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
        # 0-100 skala, delta başına max ±2 hareket (yavaş ilerleme)
        skill: max(0, min(100, current.get(skill, 50) + delta))
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
