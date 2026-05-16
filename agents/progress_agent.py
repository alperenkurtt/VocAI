from pydantic import BaseModel, Field
from typing import Optional, Dict
from state import GraphState
from database import session_history, user_profiles

LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]
LEVEL_UP_THRESHOLD = 0.85   # 3 ardışık oturumda bu skorun üstü → seviye atlama önerisi
LEVEL_UP_STREAK = 3         # Kaç ardışık oturum yüksek skor gerekiyor


class SessionSummary(BaseModel):
    session_id: str
    date: str
    cefr_level: str
    overall_score: float
    skill_deltas: Dict[str, int]
    level_up_recommendation: Optional[str] = Field(
        default=None,
        description="Seviye atlama önerisi, örn. 'B1 → B2'. Yeterli ilerleme yoksa None."
    )


def _check_level_up(sessions: list, current_level: str) -> Optional[str]:
    """Son N oturumun skoru yüksekse bir üst seviyeyi önerir."""
    if len(sessions) < LEVEL_UP_STREAK:
        return None
    recent = sessions[:LEVEL_UP_STREAK]
    scores = [s.get("evaluation", {}).get("overall_score", 0) for s in recent if s.get("evaluation")]
    if len(scores) < LEVEL_UP_STREAK:
        return None
    if all(s >= LEVEL_UP_THRESHOLD for s in scores):
        idx = LEVEL_ORDER.index(current_level) if current_level in LEVEL_ORDER else -1
        if idx >= 0 and idx < len(LEVEL_ORDER) - 1:
            next_level = LEVEL_ORDER[idx + 1]
            return f"{current_level} → {next_level}"
    return None


def progress_tracker_node(state: GraphState) -> dict:
    """
    Oturumu tamamlar, ilerlemeyi hesaplar, seviye atlama önerisi üretir.
    Ajan 5: Gelişim Takipçisi
    """
    user_id = state.get("user_id", "")
    cefr_level = state.get("cefr_level", "B1")
    evaluation = state.get("evaluation_result", {})
    session_id = state.get("session_id", "")

    # Oturumu tamamla
    if session_id:
        session_history.complete_session(session_id, evaluation)

    # Beceri puanlarını güncelle
    skill_deltas = evaluation.get("skill_deltas", {})
    if user_id and skill_deltas:
        user_profiles.update_skill_scores(user_id, skill_deltas)
        user_profiles.increment_session_count(user_id)

    # Son oturumları çek, seviye atlama kontrolü yap
    recent_sessions = session_history.get_user_sessions(user_id, limit=LEVEL_UP_STREAK) if user_id else []
    level_up = _check_level_up(recent_sessions, cefr_level)

    summary = SessionSummary(
        session_id=session_id or "",
        date=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        cefr_level=cefr_level,
        overall_score=evaluation.get("overall_score", 0.0),
        skill_deltas=skill_deltas,
        level_up_recommendation=level_up,
    )

    return {"progress_history": [summary.model_dump()]}
