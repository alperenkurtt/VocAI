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
LEVEL_UP_THRESHOLDS = {
    # min_sessions : istatistiksel güvenilirlik için minimum veri eşiği (zaman kapısı değil)
    # skill_min    : ana geçit — 0'dan başlayan skor bu eşiğe ulaşmalı (CEFR seviyesine göre)
    # readiness_min: ikincil sinyal — Ajan 4'ün ürettiği next_level_readiness ortalaması
    "A1": {"min_sessions": 8,  "avg_score": 0.72, "recent": 5,  "skill_min": 45, "readiness_min": 0.50},
    "A2": {"min_sessions": 10, "avg_score": 0.74, "recent": 6,  "skill_min": 55, "readiness_min": 0.55},
    "B1": {"min_sessions": 12, "avg_score": 0.76, "recent": 7,  "skill_min": 65, "readiness_min": 0.60},
    "B2": {"min_sessions": 15, "avg_score": 0.78, "recent": 8,  "skill_min": 75, "readiness_min": 0.65},
    "C1": {"min_sessions": 18, "avg_score": 0.81, "recent": 10, "skill_min": 85, "readiness_min": 0.70},
}

_DEFAULT_THRESHOLD = {"min_sessions": 10, "avg_score": 0.74, "recent": 6, "skill_min": 55, "readiness_min": 0.55}

# Onay aşaması için gereken başarılı oturum sayısı
_CONFIRMATION_SESSIONS_REQUIRED = 2


class SessionSummary(BaseModel):
    session_id: str
    date: str
    cefr_level: str
    overall_score: float
    skill_deltas: Dict[str, int]
    next_level_readiness: float = 0.0
    level_up_recommendation: Optional[str] = Field(
        default=None,
        description="Seviye atlama önerisi, örn. 'B1 → B2'. Yeterli ilerleme yoksa None."
    )
    level_up_applied: Optional[str] = Field(
        default=None,
        description="Gerçekten uygulanan seviye atlaması. Onay tamamlanınca dolar."
    )


def _score_volatility_ok(scores: list[float]) -> bool:
    """Skorların tutarlı olup olmadığını kontrol eder (standart sapma < 0.12)."""
    if len(scores) < 3:
        return False
    avg = sum(scores) / len(scores)
    variance = sum((s - avg) ** 2 for s in scores) / len(scores)
    return (variance ** 0.5) < 0.12


def _check_candidate_eligibility(
    sessions: list,
    current_level: str,
    skill_scores: dict,
    sessions_at_level: int,
    readiness_scores: list[float],
) -> bool:
    """
    Adaylık kriterlerini kontrol eder.
    Tüm kriterler sağlanmalı: min oturum, yüksek ortalama, tutarlılık,
    zayıf beceri yok, yeterli next_level_readiness trendi.
    """
    thresholds = LEVEL_UP_THRESHOLDS.get(current_level, _DEFAULT_THRESHOLD)
    min_sessions  = thresholds["min_sessions"]
    avg_thresh    = thresholds["avg_score"]
    recent_window = thresholds["recent"]
    skill_min     = thresholds["skill_min"]
    readiness_min = thresholds["readiness_min"]

    # Kriter 1: Mevcut seviyede yeterli oturum
    if sessions_at_level < min_sessions:
        return False

    # Kriter 2: Son N oturumun ortalama skoru (yalnızca bu seviyedeki oturumlar)
    recent = sessions[:recent_window]
    scores = [
        s.get("evaluation", {}).get("overall_score", 0)
        for s in recent
        if s.get("evaluation")
    ]
    if len(scores) < recent_window:
        return False
    avg_score = sum(scores) / len(scores)
    if avg_score < avg_thresh:
        return False

    # Kriter 3: Skor tutarlılığı — tek iyi oturum false positive üretmemeli
    if not _score_volatility_ok(scores):
        return False

    # Kriter 4: Tüm beceri skorları eşiğin üstünde
    weak = [k for k, v in skill_scores.items() if v < skill_min]
    if weak:
        return False

    # Kriter 5: Son 5 oturumun next_level_readiness ortalaması yeterli mi?
    if len(readiness_scores) >= 5:
        avg_readiness = sum(readiness_scores[-5:]) / 5
        if avg_readiness < readiness_min:
            return False

    return True


def _check_confirmation_pass(evaluation: dict, current_level: str) -> bool:
    """Onay oturumunun geçip geçmediğini kontrol eder (normal eşikten daha katı)."""
    thresholds = LEVEL_UP_THRESHOLDS.get(current_level, _DEFAULT_THRESHOLD)
    score     = evaluation.get("overall_score", 0)
    readiness = evaluation.get("next_level_readiness", 0.0)
    return score >= thresholds["avg_score"] and readiness >= thresholds["readiness_min"]


def progress_tracker_node(state: GraphState) -> dict:
    """
    Oturumu tamamlar, trend verisini günceller, 2 aşamalı seviye atlama mekanizmasını çalıştırır.
    Ajan 5: Gelişim Takipçisi
    """
    user_id    = state.get("user_id", "")
    cefr_level = state.get("cefr_level", "B1")
    evaluation = state.get("evaluation_result", {})
    session_id = state.get("session_id", "")

    # Oturumu tamamla
    if session_id:
        session_history.complete_session(session_id, evaluation)

    # Beceri puanlarını ve trend verilerini güncelle
    skill_deltas  = evaluation.get("skill_deltas", {})
    readiness_val = evaluation.get("next_level_readiness", 0.0)

    if user_id and skill_deltas:
        user_profiles.update_skill_scores(user_id, skill_deltas)
        user_profiles.increment_session_count(user_id)
        user_profiles.append_trend_data(user_id, skill_deltas, readiness_val)

    # Güncel profili çek
    profile              = user_profiles.get_user_profile(user_id) if user_id else {}
    current_skill_scores = profile.get("skill_scores", {}) if profile else {}
    sessions_at_level    = profile.get("sessions_at_current_level", 0) if profile else 0
    is_candidate         = profile.get("level_up_candidate", False) if profile else False
    readiness_scores     = profile.get("readiness_scores", []) if profile else []

    # Sadece mevcut seviyedeki oturumları al (rolling window için kritik)
    _window = LEVEL_UP_THRESHOLDS.get(cefr_level, _DEFAULT_THRESHOLD)["recent"]
    recent_sessions = (
        session_history.get_user_sessions_by_level(user_id, cefr_level, limit=_window)
        if user_id else []
    )

    level_up_recommendation: Optional[str] = None
    level_up_applied: Optional[str]        = None

    if user_id and cefr_level in LEVEL_ORDER and LEVEL_ORDER.index(cefr_level) < len(LEVEL_ORDER) - 1:
        next_level = LEVEL_ORDER[LEVEL_ORDER.index(cefr_level) + 1]

        if is_candidate:
            # --- Onay aşaması ---
            if _check_confirmation_pass(evaluation, cefr_level):
                new_count = user_profiles.increment_confirmation_count(user_id)
                if new_count >= _CONFIRMATION_SESSIONS_REQUIRED:
                    # Tüm kriterler tamam → seviye atla
                    user_profiles.promote_user_level(
                        user_id, cefr_level, next_level, sessions_at_level
                    )
                    level_up_applied = f"{cefr_level} → {next_level}"
                else:
                    # Onay devam ediyor
                    level_up_recommendation = f"{cefr_level} → {next_level}"
            else:
                # Onay başarısız → adaylığı iptal et
                user_profiles.set_level_up_candidate(user_id, False)

        elif _check_candidate_eligibility(
            recent_sessions, cefr_level, current_skill_scores, sessions_at_level, readiness_scores
        ):
            # --- Aday olma aşaması ---
            user_profiles.set_level_up_candidate(user_id, True)
            level_up_recommendation = f"{cefr_level} → {next_level}"

    summary = SessionSummary(
        session_id=session_id or "",
        date=datetime.now(timezone.utc).isoformat(),
        cefr_level=cefr_level,
        overall_score=evaluation.get("overall_score", 0.0),
        skill_deltas=skill_deltas,
        next_level_readiness=readiness_val,
        level_up_recommendation=level_up_recommendation,
        level_up_applied=level_up_applied,
    )

    return {"progress_history": [summary.model_dump()]}
