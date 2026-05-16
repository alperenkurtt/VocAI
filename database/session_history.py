import uuid
from datetime import datetime, timezone
from database.client import get_collection, ensure_collection

COLLECTION = "session_history"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _col():
    ensure_collection(COLLECTION)
    return get_collection(COLLECTION)

def create_session(user_id: str, cefr_level: str, curriculum: dict) -> str:
    """Yeni oturum kaydı oluşturur, session_id döner."""
    session_id = str(uuid.uuid4())
    _col().insert_one({
        "_id": session_id,
        "user_id": user_id,
        "cefr_level": cefr_level,
        "curriculum": curriculum,
        "content": None,
        "evaluation": None,
        "started_at": _now(),
        "completed_at": None,
    })
    return session_id

def get_session(session_id: str) -> dict | None:
    """Oturumu getirir. Bulunamazsa None döner."""
    return _col().find_one({"_id": session_id})

def get_user_sessions(user_id: str, limit: int = 5) -> list[dict]:
    """Kullanıcının son N oturumunu getirir (Ajan 5 için)."""
    cursor = _col().find(
        {"user_id": user_id},
        sort={"started_at": -1},
        limit=limit,
    )
    return list(cursor)

def update_session_content(session_id: str, content: dict) -> None:
    """Ajan 3 içerik ürettikten sonra oturuma kaydeder."""
    _col().update_one(
        {"_id": session_id},
        {"$set": {"content": content}},
    )

def complete_session(session_id: str, evaluation: dict) -> None:
    """Ajan 4 değerlendirme bitince oturumu tamamlar."""
    _col().update_one(
        {"_id": session_id},
        {"$set": {"evaluation": evaluation, "completed_at": _now()}},
    )
