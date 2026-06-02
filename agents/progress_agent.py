from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Optional, Dict
from state import GraphState
from database import session_history, user_profiles

LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]

# --- Seviye atlama kriterleri (CEFR guided-learning-hours oranlarına göre ölçeklendirildi) ---
# Kaynak: Council of Europe CEFR (2001, 2020) + Cambridge English resmi eşik tabloları
#
# Her seviyenin zorluğu bir öncekinden belirgin şekilde artar:
#   A1→A2 : ~80 öğrenme saati  (referans nokta)
#   A2→B1 : ~200 saat          (2.5x)
#   B1→B2 : ~350 saat          (4.4x)
#   B2→C1 : ~500 saat          (6.3x)
#   C1→C2 : ~700 saat          (8.8x)
#
# Bu oran farkları aşağıdaki tabloya yansıtıldı:
#   min_sessions → daha uzun bekleme (daha fazla pratik kanıtı)
#   avg_score    → daha yüksek başarı eşiği
#   recent       → tutarlılığın daha uzun pencerede ölçülmesi
#   skill_min    → tüm becerilerde daha yüksek taban puan
#
LEVEL_UP_THRESHOLDS = {
    # seviye : (min_sessions, avg_score, recent_window, skill_min)
    "A1": {"min_sessions": 15, "avg_score": 0.75, "recent": 5,  "skill_min": 62},
    "A2": {"min_sessions": 20, "avg_score": 0.78, "recent": 7,  "skill_min": 66},
    "B1": {"min_sessions": 28, "avg_score": 0.80, "recent": 8,  "skill_min": 70},
    "B2": {"min_sessions": 40, "avg_score": 0.83, "recent": 10, "skill_min": 75},
    "C1": {"min_sessions": 55, "avg_score": 0.86, "recent": 12, "skill_min": 82},
}

# C2'den yukarısı yok; geriye dönük uyumluluk için varsayılan
_DEFAULT_THRESHOLD = {"min_sessions": 15, "avg_score": 0.78, "recent": 7, "skill_min": 68}


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
    Seviye atlama için tüm kriterlerin karşılanması gerekir.
    Eşikler CEFR'in guided-learning-hours oranlarına göre seviyeye göre değişir.

    1. Mevcut seviye için minimum oturum sayısı
    2. Son N oturumun (seviyeye göre değişen pencere) yüksek ortalama skoru
    3. Tüm beceri skorlarının seviyeye özgü eşiğin üstünde olması
    """
    # Mevcut seviyenin eşik tablosunu al; tanımsız seviye için varsayılanı kullan
    thresholds = LEVEL_UP_THRESHOLDS.get(current_level, _DEFAULT_THRESHOLD)
    min_sessions = thresholds["min_sessions"]
    avg_score_thresh = thresholds["avg_score"]
    recent_window = thresholds["recent"]
    skill_min = thresholds["skill_min"]

    # Kriter 1: Mevcut seviyede tamamlanan minimum oturum sayısı
    if total_sessions < min_sessions:
        return None

    # Kriter 2: Son recent_window oturumun ortalama skoru
    recent = sessions[:recent_window]
    scores = [
        s.get("evaluation", {}).get("overall_score", 0)
        for s in recent
        if s.get("evaluation")
    ]
    if len(scores) < recent_window:
        return None
    avg_score = round(sum(scores) / len(scores), 4)
    if avg_score < avg_score_thresh:
        return None

    # Kriter 3: Tüm beceri skorları seviyeye özgü eşiğin üstünde olmalı
    if skill_scores:
        weak_skills = [k for k, v in skill_scores.items() if v < skill_min]
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

    # Son oturumları çek — pencere boyutunu mevcut seviyenin eşiğinden al
    _window = LEVEL_UP_THRESHOLDS.get(cefr_level, _DEFAULT_THRESHOLD)["recent"]
    recent_sessions = session_history.get_user_sessions(user_id, limit=_window) if user_id else []
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
