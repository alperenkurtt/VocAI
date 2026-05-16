import uuid
from database.client import get_collection, ensure_collection
from config import embeddings

COLLECTION = "rag_documents"
DIMENSION = 1536

def _col():
    ensure_collection(COLLECTION, dimension=DIMENSION)
    return get_collection(COLLECTION)

def add_document(topic: str, cefr_level: str, content: str) -> str:
    """Referans doküman ekler. Embedding otomatik hesaplanır. doc_id döner."""
    doc_id = str(uuid.uuid4())
    vector = embeddings.embed_query(content)
    _col().insert_one({
        "_id": doc_id,
        "topic": topic,
        "cefr_level": cefr_level,
        "content": content,
        "$vector": vector,
    })
    return doc_id

def search_similar(query: str, cefr_level: str, top_k: int = 3) -> list[dict]:
    """Kullanıcı cevabına en yakın referans dokümanları döner (Ajan 4 kullanır)."""
    vector = embeddings.embed_query(query)
    results = _col().find(
        {"cefr_level": cefr_level},
        sort={"$vector": vector},
        limit=top_k,
    )
    return list(results)

# Başlangıç referans dokümanları — seed_initial_docs() ile yüklenir
_SEED_DOCS = [
    ("grammar_present_simple", "A1",
     "Present simple expresses habits and facts. Form: subject + base verb (add -s/-es for he/she/it). "
     "Examples: She walks to school. I like coffee. Negative: don't/doesn't. Question: Do/Does?"),
    ("grammar_past_simple", "A2",
     "Past simple describes completed actions in the past. Regular verbs: add -ed. "
     "Examples: I walked, she played. Irregular: go→went, eat→ate. Negative: didn't + base verb."),
    ("grammar_present_perfect", "B1",
     "Present perfect links past to present. Form: have/has + past participle. "
     "Examples: I have visited Paris. She has just finished. Used with ever, never, already, yet, since, for."),
    ("grammar_conditionals", "B2",
     "Second conditional: If + past simple, would + infinitive. Expresses unreal/unlikely situations. "
     "Example: If I had more time, I would learn Spanish. Third conditional uses had + past participle and would have."),
    ("grammar_inversion", "C1",
     "Inversion for emphasis in formal contexts. Examples: Never have I seen such beauty. "
     "Rarely does she make mistakes. Not only did he lie, but he also stole. Used with negative adverbials."),
    ("grammar_subjunctive", "C2",
     "Subjunctive mood expresses wishes, hypotheticals, demands. Examples: I wish I were taller. "
     "It is essential that he be informed. The committee demanded that she resign immediately."),
    ("vocabulary_daily_life", "A1",
     "Common A1 vocabulary: house, food, water, friend, work, school, family, time, day, year, "
     "good, big, small, happy, sad, go, come, eat, drink, sleep, read, write, see, hear."),
    ("vocabulary_travel", "B1",
     "Travel vocabulary: itinerary, accommodation, departure, arrival, customs, passport, "
     "currency, reservation, transit, destination, check-in, boarding pass, luggage, delay, cancellation."),
    ("vocabulary_academic", "C1",
     "Academic vocabulary: hypothesis, methodology, empirical, theoretical, discourse, paradigm, "
     "synthesis, critique, substantiate, corroborate, ambiguous, juxtapose, elucidate, proliferate."),
    ("writing_essay_structure", "B2",
     "Essay structure: Introduction (hook + thesis), Body paragraphs (topic sentence + evidence + analysis), "
     "Conclusion (restate thesis + broader implication). Connectors: furthermore, however, in contrast, consequently."),
]

def seed_initial_docs() -> None:
    """Başlangıç referans dokümanlarını AstraDB'ye yükler. Bir kere çalıştırılır."""
    for topic, level, content in _SEED_DOCS:
        add_document(topic, level, content)
    print(f"{len(_SEED_DOCS)} doküman yüklendi.")
