import uuid
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
from api.models import RegisterRequest, LoginRequest, UserResponse
from database.user_profiles import create_user_profile, find_by_username, get_user_profile, verify_login


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
def register(body: RegisterRequest):
    if find_by_username(body.username):
        raise HTTPException(status_code=409, detail="Bu kullanıcı adı alınmış")

    user_id = str(uuid.uuid4())
    profile = create_user_profile(user_id, body.username, body.password)
    return UserResponse(
        user_id=user_id,
        username=body.username,
        cefr_level=profile["cefr_level"],
        skill_scores=profile["skill_scores"],
        total_sessions=profile["total_sessions"],
        sessions_at_current_level=profile.get("sessions_at_current_level", 0),
    )


@router.post("/login", response_model=UserResponse)
def login(body: LoginRequest):
    profile = verify_login(body.username, body.password)
    if not profile:
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı")
    return UserResponse(
        user_id=profile["_id"],
        username=profile.get("username", ""),
        cefr_level=profile["cefr_level"],
        skill_scores=profile["skill_scores"],
        total_sessions=profile["total_sessions"],
        sessions_at_current_level=profile.get("sessions_at_current_level", 0),
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        user_id=user_id,
        username=profile.get("username", ""),
        cefr_level=profile["cefr_level"],
        skill_scores=profile["skill_scores"],
        total_sessions=profile["total_sessions"],
        sessions_at_current_level=profile.get("sessions_at_current_level", 0),
    )
