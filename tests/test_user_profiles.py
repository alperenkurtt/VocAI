import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.user_profiles import (
    create_user_profile,
    get_user_profile,
    update_cefr_level,
    update_skill_scores,
    increment_session_count,
)

TEST_USER = "test_user_profile_001"

def run_test():
    print("=== user_profiles CRUD Testi ===\n")

    # Temizlik: varsa sil
    from database.client import get_collection
    get_collection("user_profiles").delete_one({"_id": TEST_USER})

    # 1. Oluştur
    profile = create_user_profile(TEST_USER)
    print(f"[1] Profil oluşturuldu: {profile}")
    assert profile["cefr_level"] == ""
    assert profile["skill_scores"]["grammar"] == 5

    # 2. Getir
    fetched = get_user_profile(TEST_USER)
    assert fetched is not None
    print(f"[2] Profil getirildi: {fetched['_id']}")

    # 3. CEFR seviyesi güncelle
    update_cefr_level(TEST_USER, "B1")
    updated = get_user_profile(TEST_USER)
    assert updated["cefr_level"] == "B1"
    print(f"[3] CEFR seviyesi güncellendi: {updated['cefr_level']}")

    # 4. Beceri puanları güncelle
    update_skill_scores(TEST_USER, {"grammar": +2, "vocabulary": -1})
    updated = get_user_profile(TEST_USER)
    assert updated["skill_scores"]["grammar"] == 7
    assert updated["skill_scores"]["vocabulary"] == 4
    print(f"[4] Beceri puanları güncellendi: {updated['skill_scores']}")

    # 5. Sınır kontrolü (10 üstüne çıkmamalı)
    update_skill_scores(TEST_USER, {"grammar": +99})
    updated = get_user_profile(TEST_USER)
    assert updated["skill_scores"]["grammar"] == 10
    print(f"[5] Üst sınır koruması çalıştı: grammar = {updated['skill_scores']['grammar']}")

    # 6. Oturum sayısı
    increment_session_count(TEST_USER)
    increment_session_count(TEST_USER)
    updated = get_user_profile(TEST_USER)
    assert updated["total_sessions"] == 2
    print(f"[6] Oturum sayısı: {updated['total_sessions']}")

    # Temizlik
    get_collection("user_profiles").delete_one({"_id": TEST_USER})
    print("\n=== TEST BAŞARIYLA TAMAMLANDI ===")

if __name__ == "__main__":
    run_test()
