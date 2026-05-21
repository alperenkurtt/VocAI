"""
RAM'de aktif assessment oturumlarını tutar.
Uygulama yeniden başlatılınca temizlenir — beklenen davranış.
"""
import threading
from langchain_core.messages import HumanMessage, AIMessage

_store: dict = {}
_lock = threading.Lock()


def create(session_id: str, user_id: str) -> None:
    with _lock:
        _store[session_id] = {
            "user_id": user_id,
            "messages": [],
            "assessment_complete": False,
            "cefr_level": "",
        }


def get(session_id: str) -> dict | None:
    with _lock:
        return _store.get(session_id)


def add_human_message(session_id: str, text: str) -> None:
    with _lock:
        if session_id in _store:
            _store[session_id]["messages"].append(HumanMessage(content=text))


def add_ai_message(session_id: str, text: str) -> None:
    with _lock:
        if session_id in _store:
            _store[session_id]["messages"].append(AIMessage(content=text))


def mark_complete(session_id: str, cefr_level: str) -> None:
    with _lock:
        if session_id in _store:
            _store[session_id]["assessment_complete"] = True
            _store[session_id]["cefr_level"] = cefr_level


def delete(session_id: str) -> None:
    with _lock:
        _store.pop(session_id, None)
