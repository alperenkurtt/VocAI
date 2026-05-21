from pydantic import BaseModel
from typing import Dict, List, Optional


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    user_id: str
    username: str
    cefr_level: str
    skill_scores: Dict[str, int]
    total_sessions: int


class AssessmentStartRequest(BaseModel):
    user_id: str


class AssessmentStartResponse(BaseModel):
    session_id: str
    initial_message: str


class AssessmentMessageRequest(BaseModel):
    session_id: str
    user_id: str
    message: str


class LessonResponse(BaseModel):
    session_id: str
    curriculum: Dict
    content: Dict


class PracticeSubmitRequest(BaseModel):
    session_id: str
    user_id: str
    answers: List[str]


class PracticeResult(BaseModel):
    evaluation: Dict
    progress: Dict


class LevelUpStartRequest(BaseModel):
    user_id: str
    target_level: str   # Hedef seviye, örn. "B2"


class LevelUpMessageRequest(BaseModel):
    session_id: str
    user_id: str
    message: str
    target_level: str
