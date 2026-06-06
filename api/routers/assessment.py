import uuid
import re
import json
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
# pyrefly: ignore [missing-import]
from fastapi.responses import StreamingResponse
from langchain_core.prompts import ChatPromptTemplate
from api.models import (
    AssessmentStartRequest, AssessmentStartResponse,
    AssessmentMessageRequest, LevelUpStartRequest, LevelUpMessageRequest,
)
from api import session_store
from agents.level_agent import system_prompt as LEVEL_SYSTEM_PROMPT
from config import llm
from database.user_profiles import get_user_profile, update_cefr_level, set_initial_skill_scores

router = APIRouter()

# --- Regular assessment patterns ---
_LEVEL_PATTERN = re.compile(r"\s*LEVEL_DETERMINED:\s*(A1|A2|B1|B2|C1|C2)")
_SKILL_PATTERN = re.compile(
    r"SKILL_SCORES:\s*grammar=(\d+)\s+vocabulary=(\d+)\s+reading=(\d+)\s+writing=(\d+)"
)

# --- Level-up assessment patterns ---
_CONFIRMED_PATTERN = re.compile(r"\s*LEVEL_CONFIRMED:\s*(A1|A2|B1|B2|C1|C2)")
_NOT_READY_PATTERN  = re.compile(r"LEVEL_NOT_READY")

# Hedef seviyeye göre test kriterleri
_LEVEL_CRITERIA = {
    "A2": "Test simple past/present, basic descriptions, short exchanges about familiar topics.",
    "B1": "Test ability to connect ideas, describe experiences, give opinions with simple reasons.",
    "B2": "Test complex sentence structures, nuanced vocabulary, arguing a point with supporting detail.",
    "C1": "Test sophisticated vocabulary, idiomatic usage, complex clause structures, abstract topics.",
    "C2": "Test near-native precision, subtle register shifts, handling ambiguity, complex argumentation.",
}

# Level-up assessment system prompt
_LEVEL_UP_PROMPT = """You are a CEFR language assessor conducting a short level-up evaluation.

Student's current level: {current_level}
Target level being tested: {target_level}

INSTRUCTIONS:
- Ask exactly 3 questions that specifically test {target_level} competencies.
- Make questions challenging enough to distinguish {current_level} from {target_level}.
- Ask ONE question at a time and wait for the response.
- After receiving all 3 answers, evaluate the student's overall performance.

EVALUATION CRITERIA FOR {target_level}:
{criteria}

AFTER 3 ANSWERS, end your final response with EXACTLY one of these signals:
  LEVEL_CONFIRMED: {target_level}    ← student clearly demonstrates {target_level} proficiency
  LEVEL_NOT_READY                    ← student needs more practice at {current_level}

Be encouraging but objective. Do not signal before receiving all 3 answers.
"""


def _chain():
    prompt = ChatPromptTemplate.from_messages([
        ("system", LEVEL_SYSTEM_PROMPT),
        ("placeholder", "{messages}"),
    ])
    return prompt | llm


def _levelup_chain(current_level: str, target_level: str):
    system = _LEVEL_UP_PROMPT.format(
        current_level=current_level,
        target_level=target_level,
        criteria=_LEVEL_CRITERIA.get(target_level, ""),
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("placeholder", "{messages}"),
    ])
    return prompt | llm


# ─────────────────────────────────────────────
# Regular assessment
# ─────────────────────────────────────────────

@router.post("/start", response_model=AssessmentStartResponse)
def start_assessment(body: AssessmentStartRequest):
    if not get_user_profile(body.user_id):
        raise HTTPException(status_code=404, detail="User not found")

    session_id = str(uuid.uuid4())
    session_store.create(session_id, body.user_id)

    response = _chain().invoke({"messages": []})
    first_question = response.content

    session_store.add_ai_message(session_id, first_question)
    return AssessmentStartResponse(session_id=session_id, initial_message=first_question)


@router.post("/message")
async def send_message(body: AssessmentMessageRequest):
    session = session_store.get(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["assessment_complete"]:
        raise HTTPException(status_code=400, detail="Assessment already complete")

    session_store.add_human_message(body.session_id, body.message)

    async def generate():
        messages = session_store.get(body.session_id)["messages"]
        full_content = ""

        async for chunk in _chain().astream({"messages": messages}):
            token = chunk.content
            if token:
                full_content += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        match = _LEVEL_PATTERN.search(full_content)
        if match:
            cefr_level = match.group(1)
            clean = _LEVEL_PATTERN.sub("", full_content)

            skill_match = _SKILL_PATTERN.search(clean)
            if skill_match:
                scores = {
                    "grammar":    min(25, int(skill_match.group(1))),
                    "vocabulary": min(25, int(skill_match.group(2))),
                    "reading":    min(25, int(skill_match.group(3))),
                    "writing":    min(25, int(skill_match.group(4))),
                }
                set_initial_skill_scores(body.user_id, scores)
                clean = _SKILL_PATTERN.sub("", clean)

            clean = clean.strip()
            final_msg = f"{clean}\n\n---\nGreat! Your English level has been determined as **{cefr_level}**."

            session_store.add_ai_message(body.session_id, final_msg)
            session_store.mark_complete(body.session_id, cefr_level)
            update_cefr_level(body.user_id, cefr_level)

            yield f"data: {json.dumps({'type': 'level_determined', 'cefr_level': cefr_level, 'final_message': final_msg})}\n\n"
        else:
            session_store.add_ai_message(body.session_id, full_content)

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ─────────────────────────────────────────────
# Level-up assessment
# ─────────────────────────────────────────────

@router.post("/levelup/start", response_model=AssessmentStartResponse)
def start_levelup_assessment(body: LevelUpStartRequest):
    profile = get_user_profile(body.user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    current_level = profile.get("cefr_level", "A1")
    session_id = str(uuid.uuid4())
    session_store.create(session_id, body.user_id)

    chain = _levelup_chain(current_level, body.target_level)
    response = chain.invoke({"messages": []})
    first_question = response.content

    session_store.add_ai_message(session_id, first_question)
    return AssessmentStartResponse(session_id=session_id, initial_message=first_question)


@router.post("/levelup/message")
async def send_levelup_message(body: LevelUpMessageRequest):
    session = session_store.get(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["assessment_complete"]:
        raise HTTPException(status_code=400, detail="Assessment already complete")

    profile = get_user_profile(body.user_id)
    current_level = profile.get("cefr_level", "A1") if profile else "A1"

    session_store.add_human_message(body.session_id, body.message)

    async def generate():
        messages = session_store.get(body.session_id)["messages"]
        full_content = ""
        chain = _levelup_chain(current_level, body.target_level)

        async for chunk in chain.astream({"messages": messages}):
            token = chunk.content
            if token:
                full_content += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        confirmed = _CONFIRMED_PATTERN.search(full_content)
        not_ready  = _NOT_READY_PATTERN.search(full_content)

        if confirmed:
            new_level = confirmed.group(1)
            clean = _CONFIRMED_PATTERN.sub("", full_content).strip()
            final_msg = f"{clean}\n\n---\n🎉 **Congratulations!** You have successfully demonstrated **{new_level}** proficiency. Your level has been updated!"

            session_store.add_ai_message(body.session_id, final_msg)
            session_store.mark_complete(body.session_id, new_level)
            update_cefr_level(body.user_id, new_level)   # DB güncelle

            yield f"data: {json.dumps({'type': 'level_up_confirmed', 'new_level': new_level, 'final_message': final_msg})}\n\n"

        elif not_ready:
            clean = _NOT_READY_PATTERN.sub("", full_content).strip()
            final_msg = f"{clean}\n\n---\nKeep practicing at **{current_level}** — you're making progress. Try again when you feel more confident!"

            session_store.add_ai_message(body.session_id, final_msg)
            session_store.mark_complete(body.session_id, current_level)

            yield f"data: {json.dumps({'type': 'level_up_failed', 'current_level': current_level, 'final_message': final_msg})}\n\n"

        else:
            session_store.add_ai_message(body.session_id, full_content)

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
