# VocAI — Claude Rehberi

## Proje Özeti
VocAI, kullanıcının İngilizce seviyesini CEFR standardına göre tespit eden ve kişiselleştirilmiş günlük ders planı üreten çok ajanlı bir öğrenme sistemidir. LangGraph üzerinde çalışır, LLM olarak OpenRouter üzerinden GPT-4o-mini kullanır, veritabanı olarak AstraDB kullanır.

---

## 5 Ajanlı Mimari

| # | Dosya | Rol | Durum |
|---|-------|-----|-------|
| 1 | `agents/level_agent.py` | Seviye Tespiti — 6-8 soruluk konuşmayla CEFR seviyesi belirler | **TAMAMLANDI** |
| 2 | `agents/curriculum_agent.py` | Müfredat Planlayıcı — CEFR seviyesine göre günlük ders planı (JSON) üretir | **TAMAMLANDI** |
| 3 | `agents/content_agent.py` | İçerik Üretici — Müfredattan gerçek ders içeriği (alıştırmalar, metinler) üretir | **YAPILACAK** |
| 4 | `agents/evaluator_agent.py` | Değerlendirici + RAG — Kullanıcı cevaplarını değerlendirir, geri bildirim verir | **YAPILACAK** |
| 5 | `agents/progress_agent.py` | Gelişim Takipçisi — Zaman içinde ilerlemeyi izler, seviye güncellemesi önerir | **YAPILACAK** |

**Akış:** Ajan 1 → Ajan 2 → Ajan 3 → Ajan 4 → Ajan 5

---

## GraphState Alanları (`state.py`)

```python
user_id: str                          # Kullanıcı kimliği
messages: List[BaseMessage]           # Konuşma geçmişi (add_messages ile birikir)
cefr_level: str                       # Tespit edilen seviye: A1/A2/B1/B2/C1/C2
assessment_complete: bool             # Ajan 1 tamamlandı mı?
daily_curriculum: Optional[Dict]      # Ajan 2 çıktısı (CurriculumPlan)
```

> Ajan 3-4-5 tamamlandıkça `state.py`'a yeni alanlar eklenecek:
> `daily_content`, `evaluation_result`, `progress_history`

---

## Dosya Yapısı

```
VocAI/
├── CLAUDE.md                   # Bu dosya
├── .env                        # API anahtarları (git'e girmiyor)
├── config.py                   # LLM ve env kurulumu
├── state.py                    # LangGraph GraphState tanımı
├── graph.py                    # 5 ajan bittikten sonra yazılacak
├── app.py                      # UI aşamasında yazılacak
│
├── agents/
│   ├── __init__.py
│   ├── level_agent.py          # Ajan 1 ✓
│   ├── curriculum_agent.py     # Ajan 2 ✓
│   ├── content_agent.py        # Ajan 3
│   ├── evaluator_agent.py      # Ajan 4
│   └── progress_agent.py       # Ajan 5
│
├── database/
│   ├── __init__.py
│   ├── client.py               # AstraDB bağlantısı
│   ├── user_profiles.py        # Kullanıcı profili CRUD
│   ├── session_history.py      # Oturum geçmişi CRUD
│   ├── error_logs.py           # Hata kayıtları
│   └── vector_store.py         # RAG için vektör işlemleri (Ajan 4)
│
├── pages/                      # UI aşamasında
│   ├── 1_Assessment.py
│   ├── 2_Dashboard.py
│   ├── 3_Daily_Lesson.py
│   └── 4_Practice.py
│
└── tests/
    ├── test_agent1.py          # ✓ — interaktif CLI testi
    ├── test_agent2.py          # ✓ — A1/B2/C1 için JSON çıktı testi
    ├── test_database.py        # ✓ — AstraDB bağlantı testi
    ├── test_agent3.py
    ├── test_agent4.py
    ├── test_agent5.py
    └── test_graph.py           # Ajan 1→2 uçtan uca ✓, tüm ajanlar sonra güncellenecek
```

---

## Testleri Çalıştırma

```bash
# Tek ajan testi (interaktif)
python tests/test_agent1.py
python tests/test_agent2.py

# Veritabanı bağlantı testi
python tests/test_database.py

# Uçtan uca entegrasyon testi (Ajan 1 → Ajan 2)
python tests/test_graph.py
```

---

## LLM Yapılandırması (`config.py`)

- **Model:** `openai/gpt-4o-mini` via OpenRouter
- **API Base:** `https://openrouter.ai/api/v1`
- Tüm ajanlar `from config import llm` ile aynı LLM instance'ını kullanır

---

## Kod Kuralları

- Ajan fonksiyonları her zaman `(state: GraphState) -> dict` imzasını taşır
- Her ajan yalnızca kendi ilgili state alanlarını döndürür, tümünü değil
- System prompt'lar ilgili ajan dosyasının en üstünde modül seviyesi string olarak tanımlanır
- Yorumlar Türkçe yazılır
- Pydantic modelleri yapılandırılmış LLM çıktıları için kullanılır (Ajan 2 örneği takip edilir)
- `database/` katmanı ajanlardan bağımsız tutulur; ajanlar doğrudan DB çağrısı yapmaz
