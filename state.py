from typing import TypedDict, Annotated, List, Dict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    """
    Projenin kalbi: LangGraph içindeki ajanların birbirleriyle haberleşirken
    kullanacağı ortak 'Durum' (State) sözlüğü.
    """
    user_id: str
    session_id: str
    messages: Annotated[List[BaseMessage], add_messages]
    cefr_level: str
    assessment_complete: bool
    daily_curriculum: Optional[Dict]
    daily_content: Optional[Dict]       # Ajan 3 çıktısı — egzersizler, metinler
    evaluation_result: Optional[Dict]   # Ajan 4 çıktısı — puanlar, geri bildirim
    progress_history: Optional[List]    # Ajan 5 çıktısı — oturum özeti
