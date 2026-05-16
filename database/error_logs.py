from datetime import datetime, timezone
from database.client import get_collection, ensure_collection

COLLECTION = "error_logs"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _col():
    ensure_collection(COLLECTION)
    return get_collection(COLLECTION)

def log_error(user_id: str, agent: str, error: str, context: dict = None) -> None:
    """Ajan hatalarını kaydeder. Ajanlar try/except bloklarında bunu çağırır."""
    _col().insert_one({
        "user_id": user_id,
        "agent": agent,
        "error": error,
        "context": context or {},
        "timestamp": _now(),
    })

def get_errors_by_user(user_id: str) -> list[dict]:
    """Kullanıcıya ait tüm hata kayıtlarını döner."""
    return list(_col().find({"user_id": user_id}))
