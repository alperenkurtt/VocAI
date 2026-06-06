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
    # ── A1 (3 doküman) ──────────────────────────────────────────────────────
    ("grammar_present_simple", "A1",
     "Present simple expresses habits and facts. Form: subject + base verb (add -s/-es for he/she/it). "
     "Examples: She walks to school. I like coffee. Negative: don't/doesn't. Question: Do/Does?"),
    ("vocabulary_daily_life", "A1",
     "Common A1 vocabulary: house, food, water, friend, work, school, family, time, day, year, "
     "good, big, small, happy, sad, go, come, eat, drink, sleep, read, write, see, hear."),
    ("reading_short_texts", "A1",
     "A1 reading skills: understand very short, simple texts such as signs, menus, timetables, and short personal messages. "
     "Key strategy: focus on familiar words and numbers. Ignore unknown words and guess from context. "
     "Example text types: shop signs, simple notes, greetings cards, short SMS messages."),

    # ── A2 (3 doküman) ──────────────────────────────────────────────────────
    ("grammar_past_simple", "A2",
     "Past simple describes completed actions in the past. Regular verbs: add -ed. "
     "Examples: I walked, she played. Irregular: go→went, eat→ate. Negative: didn't + base verb."),
    ("vocabulary_shopping", "A2",
     "A2 shopping vocabulary: price, receipt, discount, sale, size, colour, cheap, expensive, pay, cash, card, "
     "change, bag, shop assistant, queue, fitting room, exchange, refund, total, bill, cost, afford, spend."),
    ("writing_short_messages", "A2",
     "A2 writing: short, simple messages, notes, and personal emails. "
     "Structure: greeting (Hi/Dear) → main point in 1-2 sentences → closing (Thanks, See you). "
     "Use simple connectors: and, but, because, so. Keep sentences short. Avoid complex grammar."),

    # ── B1 (3 doküman) ──────────────────────────────────────────────────────
    ("grammar_present_perfect", "B1",
     "Present perfect links past to present. Form: have/has + past participle. "
     "Examples: I have visited Paris. She has just finished. Used with ever, never, already, yet, since, for."),
    ("vocabulary_travel", "B1",
     "Travel vocabulary: itinerary, accommodation, departure, arrival, customs, passport, "
     "currency, reservation, transit, destination, check-in, boarding pass, luggage, delay, cancellation."),
    ("writing_informal_email", "B1",
     "B1 informal email structure: greeting → reason for writing → main message (2-3 short paragraphs) → closing. "
     "Useful phrases: I'm writing to tell you..., I was wondering if..., Let me know what you think, "
     "Looking forward to hearing from you, Best wishes. Use contractions (I'm, it's) and friendly tone."),

    # ── B2 (3 doküman) ──────────────────────────────────────────────────────
    ("grammar_conditionals", "B2",
     "Second conditional: If + past simple, would + infinitive. Expresses unreal/unlikely situations. "
     "Example: If I had more time, I would learn Spanish. Third conditional uses had + past participle and would have."),
    ("vocabulary_business", "B2",
     "B2 business vocabulary: negotiate, deadline, stakeholder, proposal, revenue, forecast, strategy, "
     "quarterly report, profit margin, market share, competitor, implement, collaborate, delegate, prioritise, "
     "agenda, minutes, benchmark, follow up, deliverable, invoice, budget, target, KPI."),
    ("writing_essay_structure", "B2",
     "Essay structure: Introduction (hook + thesis), Body paragraphs (topic sentence + evidence + analysis), "
     "Conclusion (restate thesis + broader implication). Connectors: furthermore, however, in contrast, consequently."),

    # ── C1 (3 doküman) ──────────────────────────────────────────────────────
    ("grammar_inversion", "C1",
     "Inversion for emphasis in formal contexts. Examples: Never have I seen such beauty. "
     "Rarely does she make mistakes. Not only did he lie, but he also stole. Used with negative adverbials."),
    ("vocabulary_academic", "C1",
     "Academic vocabulary: hypothesis, methodology, empirical, theoretical, discourse, paradigm, "
     "synthesis, critique, substantiate, corroborate, ambiguous, juxtapose, elucidate, proliferate."),
    ("writing_formal_report", "C1",
     "C1 formal report: Title → Executive Summary → Introduction → Findings (with subheadings) → Conclusion → Recommendations. "
     "Impersonal passive voice preferred: 'It was found that...', 'Data suggests...'. "
     "Avoid contractions. Use hedging language: apparently, it would seem, there is evidence to suggest. "
     "Precise referencing: According to the data in Figure 1..."),

    # ── C2 (3 doküman) ──────────────────────────────────────────────────────
    ("grammar_subjunctive", "C2",
     "Subjunctive mood expresses wishes, hypotheticals, demands. Examples: I wish I were taller. "
     "It is essential that he be informed. The committee demanded that she resign immediately."),
    ("vocabulary_idiomatic", "C2",
     "C2 idiomatic and advanced collocations: beating around the bush, a double-edged sword, "
     "pour oil on troubled waters, the elephant in the room, bite the bullet, cut corners, "
     "sit on the fence, go against the grain, take with a pinch of salt, burning the midnight oil. "
     "Register shifts: 'kick the bucket' (informal) vs. 'pass away' (formal) vs. 'die' (neutral)."),
    ("writing_critical_analysis", "C2",
     "C2 critical analysis: evaluate sources, identify assumptions, expose logical fallacies. "
     "Structure: claim → evidence → counter-argument → rebuttal → nuanced conclusion. "
     "Useful phrases: One might argue..., This view is undermined by..., A more nuanced reading suggests..., "
     "The author conflates X with Y..., This raises the question of whether... "
     "Avoid absolute statements; demonstrate awareness of complexity and ambiguity."),
]

def seed_initial_docs() -> None:
    """Başlangıç referans dokümanlarını AstraDB'ye yükler. Bir kere çalıştırılır."""
    for topic, level, content in _SEED_DOCS:
        add_document(topic, level, content)
    print(f"{len(_SEED_DOCS)} doküman yüklendi (her seviyede 3: grammar + vocabulary + reading/writing).")
