# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
from api.models import LessonResponse
from database.user_profiles import get_user_profile
from database import session_history
from agents.curriculum_agent import curriculum_planner_node
from agents.content_agent import content_generation_node

router = APIRouter()


@router.get("/today", response_model=LessonResponse)
def get_today_lesson(user_id: str):
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    # Bugün için oluşturulmuş ders var mı? Varsa tekrar üretme.
    existing = session_history.get_today_session(user_id)
    if existing:
        return LessonResponse(
            session_id=existing["_id"],
            curriculum=existing["curriculum"],
            content=existing["content"],
        )

    # Seviye yoksa B1 varsayılan
    cefr_level = profile.get("cefr_level") or "B1"
    base_state = {"user_id": user_id, "cefr_level": cefr_level, "messages": []}

    # Ajan 2: Müfredat
    curriculum = curriculum_planner_node(base_state)["daily_curriculum"]

    # Ajan 3: İçerik
    content = content_generation_node({**base_state, "daily_curriculum": curriculum})["daily_content"]

    # Oturumu DB'ye kaydet
    session_id = session_history.create_session(user_id, cefr_level, curriculum)
    session_history.update_session_content(session_id, content)

    return LessonResponse(session_id=session_id, curriculum=curriculum, content=content)
