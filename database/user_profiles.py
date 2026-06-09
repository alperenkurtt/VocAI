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
            "grammar": 0,
            "vocabulary": 0,
            "reading": 0,
            "writing": 0,
        },
        "total_sessions": 0,
        # Seviye geçiş takibi
        "sessions_at_current_level": 0,
        "level_history": [],
        "level_up_candidate": False,
        "confirmation_sessions_passed": 0,
        # Trend verileri (son 10 oturum)
        "skill_trend": {"grammar": [], "vocabulary": [], "reading": [], "writing": []},
        "readiness_scores": [],
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
        # 0-100 skala, delta başına max ±1 hareket (CEFR temposuna uygun yavaş ilerleme)
        skill: max(0, min(100, current.get(skill, 0) + max(-1, min(1, delta))))
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
            "sessions_at_current_level": profile.get("sessions_at_current_level", 0) + 1,
            "last_active": _now(),
        }},
    )


def promote_user_level(user_id: str, from_level: str, to_level: str, sessions_spent: int) -> None:
    """Level-up'ı uygular, sayaçları sıfırlar, geçmişe yazar."""
    profile = get_user_profile(user_id)
    if not profile:
        return
    history_entry = {
        "level": from_level,
        "sessions": sessions_spent,
        "promoted_at": _now(),
    }
    _col().update_one(
        {"_id": user_id},
        {
            "$set": {
                "cefr_level": to_level,
                "sessions_at_current_level": 0,
                "level_up_candidate": False,
                "confirmation_sessions_passed": 0,
                "last_active": _now(),
            },
            "$push": {"level_history": history_entry},
        },
    )


def set_level_up_candidate(user_id: str, is_candidate: bool) -> None:
    """Adaylık durumunu günceller. False'a ayarlanınca onay sayacı da sıfırlanır."""
    update: dict = {"level_up_candidate": is_candidate, "last_active": _now()}
    if not is_candidate:
        update["confirmation_sessions_passed"] = 0
    _col().update_one({"_id": user_id}, {"$set": update})


def increment_confirmation_count(user_id: str) -> int:
    """Onay oturumu sayacını artırır ve güncel değeri döner."""
    profile = get_user_profile(user_id)
    if not profile:
        return 0
    new_count = profile.get("confirmation_sessions_passed", 0) + 1
    _col().update_one(
        {"_id": user_id},
        {"$set": {"confirmation_sessions_passed": new_count, "last_active": _now()}},
    )
    return new_count


def append_trend_data(user_id: str, skill_deltas: dict, readiness_score: float) -> None:
    """Trend listelerini günceller; her liste max 10 eleman tutar."""
    profile = get_user_profile(user_id)
    if not profile:
        return
    trend = profile.get("skill_trend", {k: [] for k in ["grammar", "vocabulary", "reading", "writing"]})
    readiness_history = profile.get("readiness_scores", [])

    for skill, delta in skill_deltas.items():
        if skill in trend:
            trend[skill] = (trend[skill] + [delta])[-10:]

    readiness_history = (readiness_history + [readiness_score])[-10:]

    _col().update_one(
        {"_id": user_id},
        {"$set": {"skill_trend": trend, "readiness_scores": readiness_history}},
    )


def delete_user(user_id: str) -> bool:
    """Kullanıcıyı siler. Başarılıysa True, bulunamazsa False döner."""
    result = _col().delete_one({"_id": user_id})
    return result.deleted_count > 0

def delete_user_by_username(username: str) -> bool:
    """Kullanıcı adına göre siler. Başarılıysa True döner."""
    result = _col().delete_one({"username": username})
    return result.deleted_count > 0
