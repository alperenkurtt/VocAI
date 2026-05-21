# VocAI — Claude Rehberi

## Proje Özeti
VocAI, kullanıcının İngilizce seviyesini CEFR standardına göre tespit eden ve kişiselleştirilmiş günlük ders planı üreten çok ajanlı bir öğrenme sistemidir. LangGraph üzerinde çalışır, LLM olarak OpenRouter üzerinden GPT-4o-mini kullanır, veritabanı olarak AstraDB kullanır.

**Backend:** FastAPI (`api/`)
**Mobil:** React Native (Expo) — yapım aşamasında
**Eski UI:** Streamlit kaldırıldı

---

## 5 Ajanlı Mimari

| # | Dosya | Rol | Durum |
|---|-------|-----|-------|
| 1 | `agents/level_agent.py` | Seviye Tespiti — 4-5 soruluk konuşmayla CEFR seviyesi belirler | **TAMAMLANDI** |
| 2 | `agents/curriculum_agent.py` | Müfredat Planlayıcı — CEFR seviyesine göre günlük ders planı (JSON) üretir | **TAMAMLANDI** |
| 3 | `agents/content_agent.py` | İçerik Üretici — Müfredattan gerçek ders içeriği (5-7 egzersiz, okuma metni) üretir | **TAMAMLANDI** |
| 4 | `agents/evaluator_agent.py` | Değerlendirici + RAG — Kullanıcı cevaplarını değerlendirir, Türkçe geri bildirim verir | **TAMAMLANDI** |
| 5 | `agents/progress_agent.py` | Gelişim Takipçisi — Oturumu kaydeder, seviye atlama önerisi üretir | **TAMAMLANDI** |

**Akış:** Ajan 1 → Ajan 2 → Ajan 3 → Ajan 4 → Ajan 5

---

## GraphState Alanları (`state.py`)

```python
user_id: str                          # Kullanıcı kimliği
session_id: str                       # Aktif oturum ID'si (AstraDB'de session_history)
messages: List[BaseMessage]           # Konuşma geçmişi (add_messages ile birikir)
cefr_level: str                       # Tespit edilen seviye: A1/A2/B1/B2/C1/C2
assessment_complete: bool             # Ajan 1 tamamlandı mı?
daily_curriculum: Optional[Dict]      # Ajan 2 çıktısı (CurriculumPlan)
daily_content: Optional[Dict]         # Ajan 3 çıktısı (DailyContent)
evaluation_result: Optional[Dict]     # Ajan 4 çıktısı (EvaluationResult)
progress_history: Optional[List]      # Ajan 5 çıktısı (SessionSummary listesi)
```

---

## Dosya Yapısı

```
VocAI/
├── CLAUDE.md                   # Bu dosya
├── .env                        # API anahtarları (git'e girmiyor)
├── config.py                   # LLM + embeddings kurulumu
├── state.py                    # LangGraph GraphState tanımı
├── graph.py                    # 5 ajanlı LangGraph pipeline
│
├── agents/
│   ├── __init__.py
│   ├── level_agent.py          # Ajan 1 ✓
│   ├── curriculum_agent.py     # Ajan 2 ✓
│   ├── content_agent.py        # Ajan 3 ✓
│   ├── evaluator_agent.py      # Ajan 4 ✓ (RAG)
│   └── progress_agent.py       # Ajan 5 ✓
│
├── database/
│   ├── __init__.py
│   ├── client.py               # AstraDB bağlantısı + ensure_collection
│   ├── user_profiles.py        # Kullanıcı profili CRUD
│   ├── session_history.py      # Oturum geçmişi CRUD
│   ├── error_logs.py           # Hata kayıtları
│   └── vector_store.py         # RAG için vektör işlemleri (10 seed doc yüklü)
│
├── api/                        # FastAPI backend
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, CORS, router kayıtları
│   ├── models.py               # Request/Response Pydantic modelleri
│   ├── session_store.py        # RAM'de konuşma geçmişi (Ajan 1 için)
│   └── routers/
│       ├── __init__.py
│       ├── users.py            # POST /users/register, /users/login
│       ├── assessment.py       # POST /assessment/start, /assessment/message (SSE)
│       ├── lesson.py           # GET /lesson/today
│       └── practice.py         # POST /practice/submit
│
└── tests/
    ├── test_agent1.py          # ✓ interaktif CLI testi
    ├── test_agent2.py          # ✓ A1/B2/C1 JSON çıktı testi
    ├── test_agent3.py          # ✓ B1 içerik üretimi testi
    ├── test_agent4.py          # ✓ RAG değerlendirme testi
    ├── test_agent5.py          # ✓ ilerleme testi
    ├── test_database.py        # ✓ AstraDB bağlantı testi
    ├── test_session_history.py # ✓ oturum CRUD testi
    ├── test_vector_store.py    # ✓ embedding + vektör arama testi
    └── test_graph.py           # ✓ Ajan 1→5 uçtan uca + pipeline testi
```

---

## API'yi Çalıştırma

```bash
uvicorn api.main:app --reload
# Swagger UI: http://localhost:8000/docs
```

## Testleri Çalıştırma

```bash
# Tek ajan testleri
python -m tests.test_agent3
python -m tests.test_agent4
python -m tests.test_agent5

# Database testleri
python -m tests.test_session_history
python -m tests.test_vector_store

# Uçtan uca pipeline testi (Ajan 2→3→4→5, otomatik)
python tests/test_graph.py --pipeline

# İnteraktif tam test (Ajan 1→5, klavye girişi)
python tests/test_graph.py
```

---

## LLM ve Embedding Yapılandırması (`config.py`)

- **LLM:** `openai/gpt-4o-mini` via OpenRouter
- **Embeddings:** `openai/text-embedding-3-small` via OpenRouter (dim=1536)
- **API Base:** `https://openrouter.ai/api/v1`
- Tüm ajanlar `from config import llm` ile aynı instance'ı kullanır
- `database/vector_store.py` `from config import embeddings` ile embedding yapar

---

## AstraDB Koleksiyonları

| Koleksiyon | Modül | Açıklama |
|------------|-------|----------|
| `user_profiles` | `database/user_profiles.py` | Kullanıcı profili, skill skorları |
| `session_history` | `database/session_history.py` | Oturum kayıtları |
| `error_logs` | `database/error_logs.py` | Ajan hata logları |
| `rag_documents` | `database/vector_store.py` | RAG referans dokümanlar (vektör, dim=1536) |

Tüm koleksiyonlar `ensure_collection()` ile otomatik oluşturulur.

---

## Kod Kuralları

- Ajan fonksiyonları her zaman `(state: GraphState) -> dict` imzasını taşır
- Her ajan yalnızca kendi ilgili state alanlarını döndürür, tümünü değil
- System prompt'lar ilgili ajan dosyasının en üstünde modül seviyesi string olarak tanımlanır
- Yorumlar Türkçe yazılır
- Pydantic modelleri yapılandırılmış LLM çıktıları için kullanılır
- `database/` katmanı ajanlardan bağımsız tutulur; ajanlar doğrudan DB çağrısı yapmaz
- `api/` katmanı ajanları ve database'i çağırır; iş mantığı buraya taşınmaz
