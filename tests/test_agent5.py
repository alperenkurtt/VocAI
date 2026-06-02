import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows terminali UTF-8 olarak ayarla
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

"""
Ajan 5 — Kapsamlı Test Paketi
==============================
Çalıştırma: python -m tests.test_agent5

Test Bölümleri:
  1. CEFR Eşik Tablosu Doğrulama   — eşikler gerçekten seviyeyle artıyor mu?
  2. Kriter 1: Minimum Oturum       — yeterli oturum yokken atlama engelleniyor mu?
  3. Kriter 2: Ortalama Skor        — düşük / yetersiz oturum sayısı engelleniyor mu?
  4. Kriter 3: Beceri Skorları       — zayıf beceri varken atlama engelleniyor mu?
  5. Senaryo Testleri               — her seviye için "tam geçer / tam kalır" tablosu
  6. Köşe Durumlar                  — C2, tanımsız seviye, boş skill_scores
  7. Entegrasyon                    — progress_tracker_node çıktı yapısı

Toplam: 30 test senaryosu
"""

# Database katmanı ve harici bağımlılıklar mock'lanıyor;
# bu testler ağ/DB erişimi olmadan çalışır.
from unittest.mock import MagicMock, patch
import sys

_mock_session_history = MagicMock()
_mock_user_profiles   = MagicMock()
_mock_db_module       = MagicMock()
_mock_db_module.session_history = _mock_session_history
_mock_db_module.user_profiles   = _mock_user_profiles

sys.modules.setdefault("astrapy",          MagicMock())
sys.modules.setdefault("database",         _mock_db_module)
sys.modules.setdefault("database.client",  MagicMock())
sys.modules.setdefault("database.session_history", _mock_session_history)
sys.modules.setdefault("database.user_profiles",   _mock_user_profiles)

from agents.progress_agent import (
    _check_level_up,
    progress_tracker_node,
    LEVEL_UP_THRESHOLDS,
    LEVEL_ORDER,
    _DEFAULT_THRESHOLD,
)

# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------------------

def make_sessions(n: int, score: float) -> list:
    """n adet, belirtilen skorla tamamlanmış sahte oturum listesi üretir."""
    return [
        {
            "evaluation": {
                "overall_score": score,
                "skill_deltas": {},
                "feedback": "test",
                "correct_answers": int(score * 10),
                "total_questions": 10,
            },
            "started_at": f"2024-01-{i+1:02d}T10:00:00Z",
        }
        for i in range(n)
    ]


def all_skills(value: int) -> dict:
    """Dört becerinin hepsini aynı değere ayarlar."""
    return {"grammar": value, "vocabulary": value, "reading": value, "writing": value}


def make_state(score: float, cefr: str = "B1", user_id: str = "") -> dict:
    """progress_tracker_node için minimal state üretir."""
    return {
        "user_id": user_id,
        "cefr_level": cefr,
        "session_id": "",
        "assessment_complete": True,
        "messages": [],
        "daily_curriculum": None,
        "daily_content": None,
        "evaluation_result": {
            "overall_score": score,
            "skill_deltas": {"grammar": 1, "vocabulary": 0, "reading": 0, "writing": 0},
            "feedback": "Test geri bildirimi",
            "correct_answers": int(score * 10),
            "total_questions": 10,
            "rag_references": [],
        },
        "progress_history": None,
    }


PASS = "✅"
FAIL = "❌"
SEP  = "-" * 60

# ---------------------------------------------------------------------------
# 1. CEFR Eşik Tablosu Doğrulama
# ---------------------------------------------------------------------------

def test_thresholds_increase_with_level():
    """
    CEFR'in guided-learning-hours tablosuna göre her eşik bir üst
    seviyede büyük ya da eşit olmalıdır — hiçbiri küçük olmamalı.
    """
    print(SEP)
    print("BÖLÜM 1 — CEFR Eşik Tablosu Doğrulama")
    print(SEP)

    levels_in_order = ["A1", "A2", "B1", "B2", "C1"]
    keys = ["min_sessions", "avg_score", "recent", "skill_min"]

    for i in range(len(levels_in_order) - 1):
        lower = levels_in_order[i]
        upper = levels_in_order[i + 1]
        for key in keys:
            v_lower = LEVEL_UP_THRESHOLDS[lower][key]
            v_upper = LEVEL_UP_THRESHOLDS[upper][key]
            assert v_upper >= v_lower, (
                f"{upper}.{key} ({v_upper}) < {lower}.{key} ({v_lower}) — CEFR'e aykırı!"
            )
            print(f"  {PASS} {lower}→{upper} | {key}: {v_lower} → {v_upper}")

    # Tam monoton artış (sadece eşit değil, gerçekten büyük mü?)
    for key in ["min_sessions", "skill_min"]:
        values = [LEVEL_UP_THRESHOLDS[lv][key] for lv in levels_in_order]
        assert values == sorted(set(values)), (
            f"{key} tüm seviyelerde kesinlikle artmalı: {values}"
        )
    print(f"\n  {PASS} Tüm eşikler CEFR sıralamasıyla uyumlu.")


# ---------------------------------------------------------------------------
# 2. Kriter 1 — Minimum Oturum Sayısı
# ---------------------------------------------------------------------------

def test_criterion1_insufficient_sessions():
    """Her seviye için minimum oturumun 1 eksiği → atlama olmamalı."""
    print(f"\n{SEP}")
    print("BÖLÜM 2 — Kriter 1: Minimum Oturum Sayısı")
    print(SEP)

    for level, th in LEVEL_UP_THRESHOLDS.items():
        needed = th["min_sessions"]
        window = th["recent"]
        sessions = make_sessions(window, 0.99)          # skor yeterli
        skills   = all_skills(th["skill_min"] + 5)     # beceriler yeterli

        result = _check_level_up(sessions, level, skills, total_sessions=needed - 1)
        assert result is None, f"{level}: {needed-1} oturumda seviye atlamalıydı!"
        print(f"  {PASS} {level} | {needed-1}/{needed} oturum → öneri YOK")


def test_criterion1_exact_sessions():
    """Tam minimum oturum sayısında (diğer kriterler tamam) → atlama önerisi gelmeli."""
    print()
    for level, th in LEVEL_UP_THRESHOLDS.items():
        needed = th["min_sessions"]
        window = th["recent"]
        sessions = make_sessions(window, th["avg_score"] + 0.05)
        skills   = all_skills(th["skill_min"] + 5)

        result = _check_level_up(sessions, level, skills, total_sessions=needed)
        expected_next = LEVEL_ORDER[LEVEL_ORDER.index(level) + 1]
        assert result == f"{level} → {expected_next}", (
            f"{level}: Tam oturumda öneri beklendi, gelen: {result}"
        )
        print(f"  {PASS} {level} | {needed}/{needed} oturum + diğerleri tamam → {result}")


# ---------------------------------------------------------------------------
# 3. Kriter 2 — Son N Oturumun Ortalama Skoru
# ---------------------------------------------------------------------------

def test_criterion2_low_avg_score():
    """Ortalama skoru eşiğin hemen altında → atlama olmamalı."""
    print(f"\n{SEP}")
    print("BÖLÜM 3 — Kriter 2: Ortalama Skor Eşiği")
    print(SEP)

    for level, th in LEVEL_UP_THRESHOLDS.items():
        window   = th["recent"]
        low_score = round(th["avg_score"] - 0.01, 4)
        sessions = make_sessions(window, low_score)
        skills   = all_skills(th["skill_min"] + 5)

        result = _check_level_up(sessions, level, skills, total_sessions=th["min_sessions"])
        assert result is None, f"{level}: {low_score} ortalama skorda atlama olmaz!"
        print(f"  {PASS} {level} | ort. {low_score:.2f} < {th['avg_score']} → öneri YOK")


def test_criterion2_exact_avg_score():
    """Tam eşik skoru (diğer kriterler tamam) → atlama önerisi gelmeli."""
    print()
    for level, th in LEVEL_UP_THRESHOLDS.items():
        window   = th["recent"]
        sessions = make_sessions(window, th["avg_score"])
        skills   = all_skills(th["skill_min"] + 5)

        result = _check_level_up(sessions, level, skills, total_sessions=th["min_sessions"])
        expected_next = LEVEL_ORDER[LEVEL_ORDER.index(level) + 1]
        assert result == f"{level} → {expected_next}", (
            f"{level}: Tam skor eşiğinde öneri beklendi, gelen: {result}"
        )
        print(f"  {PASS} {level} | ort. {th['avg_score']:.2f} (tam eşik) → {result}")


def test_criterion2_insufficient_evaluated_sessions():
    """
    Toplam oturum sayısı yeterli ama değerlendirmesi olan oturum
    recent_window'dan az → pencere doldurulamaz → atlama olmamalı.
    """
    print()
    level = "B1"
    th    = LEVEL_UP_THRESHOLDS[level]
    # Değerlendirmesi OLMAYAN oturumlar
    empty_sessions = [{"started_at": "2024-01-01T00:00:00Z"} for _ in range(th["recent"])]
    skills = all_skills(th["skill_min"] + 5)

    result = _check_level_up(empty_sessions, level, skills, total_sessions=th["min_sessions"])
    assert result is None
    print(f"  {PASS} {level} | {th['recent']} oturum değerlendirmesiz → öneri YOK")


# ---------------------------------------------------------------------------
# 4. Kriter 3 — Beceri Skorları
# ---------------------------------------------------------------------------

def test_criterion3_one_weak_skill():
    """Tek bir beceri eşiğin altındaysa → atlama olmamalı."""
    print(f"\n{SEP}")
    print("BÖLÜM 4 — Kriter 3: Beceri Skorları")
    print(SEP)

    skill_names = ["grammar", "vocabulary", "reading", "writing"]
    level = "B1"
    th    = LEVEL_UP_THRESHOLDS[level]
    sessions = make_sessions(th["recent"], th["avg_score"] + 0.05)

    for weak in skill_names:
        skills = all_skills(th["skill_min"] + 5)
        skills[weak] = th["skill_min"] - 1   # sadece bu beceri zayıf

        result = _check_level_up(sessions, level, skills, total_sessions=th["min_sessions"])
        assert result is None, f"{weak} zayıfken atlama olmaz!"
        print(f"  {PASS} {level} | '{weak}' = {skills[weak]} (eşik {th['skill_min']}) → öneri YOK")


def test_criterion3_all_skills_at_threshold():
    """Tüm beceriler tam eşikte (diğer kriterler tamam) → atlama gelmeli."""
    print()
    level = "A2"
    th    = LEVEL_UP_THRESHOLDS[level]
    sessions = make_sessions(th["recent"], th["avg_score"] + 0.05)
    skills   = all_skills(th["skill_min"])   # tam eşikte

    result = _check_level_up(sessions, level, skills, total_sessions=th["min_sessions"])
    expected_next = LEVEL_ORDER[LEVEL_ORDER.index(level) + 1]
    assert result == f"{level} → {expected_next}"
    print(f"  {PASS} {level} | tüm beceriler tam eşikte ({th['skill_min']}) → {result}")


def test_criterion3_empty_skill_scores():
    """skill_scores boş sözlük → kriter 3 atlanır, diğerleri tamam ise atlama olur."""
    level = "A1"
    th    = LEVEL_UP_THRESHOLDS[level]
    sessions = make_sessions(th["recent"], th["avg_score"] + 0.05)

    result = _check_level_up(sessions, level, skill_scores={}, total_sessions=th["min_sessions"])
    expected_next = LEVEL_ORDER[LEVEL_ORDER.index(level) + 1]
    assert result == f"{level} → {expected_next}"
    print(f"  {PASS} {level} | boş skill_scores → kriter 3 atlandı → {result}")


# ---------------------------------------------------------------------------
# 5. Senaryo Testleri — Seviyeye Göre Tam Geçer / Tam Kalır
# ---------------------------------------------------------------------------

def test_scenarios_all_levels():
    """
    Her CEFR seviyesi için iki senaryo:
      A) Tam kriterleri karşılayan → atlama beklenir
      B) Oturum sayısı yetersiz    → atlama beklenmez
    """
    print(f"\n{SEP}")
    print("BÖLÜM 5 — Senaryo Testleri (Geçer / Kalır)")
    print(SEP)
    print(f"  {'Seviye':<6} {'Senaryo':<35} {'Beklenen':<12} {'Sonuç'}")
    print(f"  {'-'*6} {'-'*35} {'-'*12} {'-'*10}")

    for level, th in LEVEL_UP_THRESHOLDS.items():
        next_level = LEVEL_ORDER[LEVEL_ORDER.index(level) + 1]
        sessions_ok  = make_sessions(th["recent"], th["avg_score"] + 0.05)
        skills_ok    = all_skills(th["skill_min"] + 5)

        # Senaryo A: Her şey tamam → atlamalı
        r = _check_level_up(sessions_ok, level, skills_ok, th["min_sessions"])
        expected = f"{level} → {next_level}"
        status = PASS if r == expected else FAIL
        print(f"  {level:<6} {'Tüm kriterler tamam':<35} {expected:<12} {status} gelen: {r}")
        assert r == expected, f"Senaryo A başarısız: {level}"

        # Senaryo B: 1 oturum eksik → atlamaz
        r = _check_level_up(sessions_ok, level, skills_ok, th["min_sessions"] - 1)
        status = PASS if r is None else FAIL
        senaryo_b = f"Oturum {th['min_sessions']-1}/{th['min_sessions']}"
        print(f"  {level:<6} {senaryo_b:<35} {'None':<12} {status} gelen: {r}")
        assert r is None, f"Senaryo B başarısız: {level}"


# ---------------------------------------------------------------------------
# 6. Köşe Durumlar
# ---------------------------------------------------------------------------

def test_edge_c2_no_level_up():
    """C2 en üst seviye — atlama önerisi hiçbir zaman gelmemeli."""
    print(f"\n{SEP}")
    print("BÖLÜM 6 — Köşe Durumlar")
    print(SEP)

    sessions = make_sessions(12, 0.99)
    skills   = all_skills(100)
    result   = _check_level_up(sessions, "C2", skills, total_sessions=999)
    assert result is None
    print(f"  {PASS} C2 seviyesinde seviye atlama önerisi yok (üst seviye yok)")


def test_edge_unknown_level_uses_default():
    """Tanımsız seviye kodu → varsayılan eşik kullanılır, atlama önerisi None döner."""
    sessions = make_sessions(
        _DEFAULT_THRESHOLD["recent"],
        _DEFAULT_THRESHOLD["avg_score"] + 0.05,
    )
    skills = all_skills(_DEFAULT_THRESHOLD["skill_min"] + 5)

    result = _check_level_up(
        sessions, "XX", skills,
        total_sessions=_DEFAULT_THRESHOLD["min_sessions"]
    )
    # "XX" LEVEL_ORDER'da olmadığından idx=-1 → None beklenir
    assert result is None
    print(f"  {PASS} Tanımsız seviye 'XX' → atlama önerisi yok (LEVEL_ORDER'da değil)")


def test_edge_empty_sessions_list():
    """Oturum listesi tamamen boş → yeterli pencere yok → atlama olmamalı."""
    level  = "A1"
    th     = LEVEL_UP_THRESHOLDS[level]
    result = _check_level_up([], level, all_skills(99), total_sessions=th["min_sessions"])
    assert result is None
    print(f"  {PASS} Boş oturum listesi → pencere doldurulamadı → öneri YOK")


def test_edge_multiple_weak_skills():
    """Birden fazla zayıf beceri → her biri ayrı ayrı engel oluşturmalı."""
    level    = "B2"
    th       = LEVEL_UP_THRESHOLDS[level]
    sessions = make_sessions(th["recent"], th["avg_score"] + 0.05)
    skills   = {
        "grammar":    th["skill_min"] - 5,   # zayıf
        "vocabulary": th["skill_min"] - 3,   # zayıf
        "reading":    th["skill_min"] + 10,  # yeterli
        "writing":    th["skill_min"] + 10,  # yeterli
    }
    result = _check_level_up(sessions, level, skills, total_sessions=th["min_sessions"])
    assert result is None
    print(f"  {PASS} {level} | grammar + vocabulary zayıf → öneri YOK")


# ---------------------------------------------------------------------------
# 7. Entegrasyon — progress_tracker_node çıktı yapısı
# ---------------------------------------------------------------------------

def test_integration_output_structure():
    """progress_tracker_node çıktısı doğru alanlara sahip olmalı."""
    print(f"\n{SEP}")
    print("BÖLÜM 7 — Entegrasyon: progress_tracker_node")
    print(SEP)

    result  = progress_tracker_node(make_state(0.70, cefr="B1"))
    history = result["progress_history"]

    assert isinstance(history, list) and len(history) == 1
    summary = history[0]

    required_fields = ["session_id", "date", "cefr_level", "overall_score",
                       "skill_deltas", "level_up_recommendation"]
    for field in required_fields:
        assert field in summary, f"Eksik alan: {field}"

    assert summary["cefr_level"] == "B1"
    assert 0.0 <= summary["overall_score"] <= 1.0
    assert isinstance(summary["skill_deltas"], dict)
    print(f"  {PASS} Tüm zorunlu alanlar mevcut: {required_fields}")


def test_integration_low_score_no_recommendation():
    """Düşük skor + user_id yok → seviye atlama önerisi gelmemeli."""
    result  = progress_tracker_node(make_state(0.40, cefr="A2"))
    summary = result["progress_history"][0]
    assert summary["level_up_recommendation"] is None
    print(f"  {PASS} Düşük skor (0.40) → level_up_recommendation = None")


def test_integration_no_user_no_recommendation():
    """user_id boş → DB çağrısı yapılamaz → öneri None olmalı."""
    result  = progress_tracker_node(make_state(0.99, cefr="A1", user_id=""))
    summary = result["progress_history"][0]
    assert summary["level_up_recommendation"] is None
    print(f"  {PASS} user_id boş → level_up_recommendation = None")


def test_integration_score_stored_correctly():
    """overall_score state'ten aynen summary'ye aktarılmalı."""
    for score in [0.0, 0.5, 0.78, 1.0]:
        result  = progress_tracker_node(make_state(score))
        summary = result["progress_history"][0]
        assert summary["overall_score"] == score, f"Skor eşleşmedi: {score}"
    print(f"  {PASS} overall_score doğru aktarılıyor (0.0 / 0.5 / 0.78 / 1.0)")


# ---------------------------------------------------------------------------
# Koşucu
# ---------------------------------------------------------------------------

def run_all():
    tests = [
        # Bölüm 1
        test_thresholds_increase_with_level,
        # Bölüm 2
        test_criterion1_insufficient_sessions,
        test_criterion1_exact_sessions,
        # Bölüm 3
        test_criterion2_low_avg_score,
        test_criterion2_exact_avg_score,
        test_criterion2_insufficient_evaluated_sessions,
        # Bölüm 4
        test_criterion3_one_weak_skill,
        test_criterion3_all_skills_at_threshold,
        test_criterion3_empty_skill_scores,
        # Bölüm 5
        test_scenarios_all_levels,
        # Bölüm 6
        test_edge_c2_no_level_up,
        test_edge_unknown_level_uses_default,
        test_edge_empty_sessions_list,
        test_edge_multiple_weak_skills,
        # Bölüm 7
        test_integration_output_structure,
        test_integration_low_score_no_recommendation,
        test_integration_no_user_no_recommendation,
        test_integration_score_stored_correctly,
    ]

    passed = 0
    failed = 0
    errors = []

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            failed += 1
            errors.append((test_fn.__name__, str(e)))
        except Exception as e:
            failed += 1
            errors.append((test_fn.__name__, f"HATA: {e}"))

    print(f"\n{'='*60}")
    print(f"SONUÇ: {passed} geçti  |  {failed} başarısız  |  toplam {passed+failed}")
    if errors:
        print("\nBaşarısız testler:")
        for name, msg in errors:
            print(f"  {FAIL} {name}: {msg}")
    else:
        print("Tüm testler başarıyla geçti. 🎉")
    print("="*60)

    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
