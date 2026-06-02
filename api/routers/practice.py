# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
from api.models import PracticeSubmitRequest, PracticeResult
from database.user_profiles import get_user_profile
from database import session_history
from agents.evaluator_agent import evaluator_node
from agents.progress_agent import progress_tracker_node

router = APIRouter()


@router.post("/submit", response_model=PracticeResult)
def submit_practice(body: PracticeSubmitRequest):
    db_session = session_history.get_session(body.session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    profile = get_user_profile(body.user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    cefr_level = profile.get("cefr_level") or "B1"

    state = {
        "user_id": body.user_id,
        "session_id": body.session_id,
        "cefr_level": cefr_level,
        "messages": [HumanMessage(content=ans) for ans in body.answers],
        "daily_content": db_session.get("content", {}),
        "daily_curriculum": db_session.get("curriculum", {}),
        "evaluation_result": None,
        "progress_history": None,
    }

    # Ajan 4: Değerlendirme
    eval_result = evaluator_node(state)
    state = {**state, **eval_result}

    # Ajan 5: İlerleme
    progress_result = progress_tracker_node(state)

    # Oturumu tamamlandı olarak işaretle — bir sonraki pratik yeni içerik üretir
    session_history.complete_session(body.session_id, eval_result["evaluation_result"])

    return PracticeResult(
        evaluation=eval_result["evaluation_result"],
        progress=progress_result["progress_history"][0],
    )
