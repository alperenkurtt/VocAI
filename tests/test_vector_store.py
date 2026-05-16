import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Vector store testi — embedding + AstraDB vektör arama.
Çalıştırma: python tests/test_vector_store.py

NOT: İlk çalıştırmada AstraDB'de 'rag_documents' koleksiyonu oluşturulur.
     OpenRouter'ın embedding endpoint'ini kullanır (openai/text-embedding-3-small).
"""
from database.vector_store import add_document, search_similar
from database.client import get_collection


def cleanup(doc_id: str) -> None:
    get_collection("rag_documents").delete_one({"_id": doc_id})


def test_embedding_and_search():
    print("1. Embedding test edilecek — doküman ekleniyor...")
    doc_id = add_document(
        topic="grammar_test",
        cefr_level="B1",
        content="Present perfect tense is used to describe past actions with present relevance. Example: I have studied English for 3 years.",
    )
    assert doc_id, "doc_id boş olmamalı"
    print(f"   doc_id: {doc_id}")

    print("2. Benzer doküman aranıyor...")
    results = search_similar(
        query="How do I use present perfect in English?",
        cefr_level="B1",
        top_k=1,
    )
    assert len(results) >= 1, "En az 1 sonuç dönmeli"
    print(f"   Bulunan: {results[0]['topic']} — {results[0]['content'][:60]}...")

    cleanup(doc_id)
    print("\nVector store testi başarılı.")


if __name__ == "__main__":
    test_embedding_and_search()
