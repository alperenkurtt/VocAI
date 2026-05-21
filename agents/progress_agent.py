from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Optional, Dict
from state import GraphState
from database import session_history, user_profiles

LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]

# --- Seviye atlama kriterleri (CEFR'e uygun, kasıtlı yüksek eşik) ---
# Son LEVEL_UP_RECENT oturumun ORTALAMASININ bu değerin üstünde olması gerekir
LEVEL_UP_AVG_SCORE   = 0.78
# Kontrol edilecek son oturum sayısı
LEVEL_UP_RECENT      = 7
# Kullanıcının mevcut seviyede tamamlamış olması gereken minimum oturum sayısı
LEVEL_UP_MIN_SESSIONS = 15
# Tüm beceri skorlarının (0-100 skalasında) bu değerin üstünde olması gerekir
LEVEL_UP_SKILL_MIN   = 68


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


def _check_level_up(
    sessions: list,
    current_level: str,
    skill_scores: dict,
    total_sessions: int,
) -> Optional[str]:
    """
    Seviye atlama için tüm kriterlerin karşılanması gerekir:
    1. Yeterli toplam oturum sayısı
    2. Son N oturumun yüksek ortalama skoru
    3. Tüm beceri skorlarının belirli eşiğin üstünde olması
    """
    # Kriter 1: Minimum oturum sayısı
    if total_sessions < LEVEL_UP_MIN_SESSIONS:
        return None

    # Kriter 2: Son LEVEL_UP_RECENT oturumun ortalama skoru
    recent = sessions[:LEVEL_UP_RECENT]
    scores = [
        s.get("evaluation", {}).get("overall_score", 0)
        for s in recent
        if s.get("evaluation")
    ]
    if len(scores) < LEVEL_UP_RECENT:
        return None
    avg_score = sum(scores) / len(scores)
    if avg_score < LEVEL_UP_AVG_SCORE:
        return None

    # Kriter 3: Tüm beceri skorları eşiğin üstünde olmalı
    if skill_scores:
        weak_skills = [k for k, v in skill_scores.items() if v < LEVEL_UP_SKILL_MIN]
        if weak_skills:
            return None

    # Tüm kriterler karşılandı → bir üst seviye öner
    idx = LEVEL_ORDER.index(current_level) if current_level in LEVEL_ORDER else -1
    if idx >= 0 and idx < len(LEVEL_ORDER) - 1:
        return f"{current_level} → {LEVEL_ORDER[idx + 1]}"
    return None


def progress_tracker_node(state: GraphState) -> dict:
    """
    Oturumu tamamlar, ilerlemeyi hesaplar, seviye atlama önerisi üretir.
    Ajan 5: Gelişim Takipçisi
    """
    user_id    = state.get("user_id", "")
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

    # Güncel profili çek (güncellenmiş skorlarla)
    profile = user_profiles.get_user_profile(user_id) if user_id else {}
    current_skill_scores = profile.get("skill_scores", {}) if profile else {}
    total_sessions = profile.get("total_sessions", 0) if profile else 0

    # Son oturumları çek, seviye atlama kontrolü yap
    recent_sessions = session_history.get_user_sessions(user_id, limit=LEVEL_UP_RECENT) if user_id else []
    level_up = _check_level_up(recent_sessions, cefr_level, current_skill_scores, total_sessions)

    summary = SessionSummary(
        session_id=session_id or "",
        date=datetime.now(timezone.utc).isoformat(),
        cefr_level=cefr_level,
        overall_score=evaluation.get("overall_score", 0.0),
        skill_deltas=skill_deltas,
        level_up_recommendation=level_up,
    )

    return {"progress_history": [summary.model_dump()]}
