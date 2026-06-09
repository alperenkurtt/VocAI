from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Dict, List
from config import llm
from state import GraphState
from database.vector_store import search_similar

EVALUATOR_SYSTEM_PROMPT = """You are an expert English language evaluator.

Student CEFR level: {cefr_level}
Today's exercises:
{exercises}

Student's answers from the conversation:
{student_answers}

Reference material for this level (use these to inform your evaluation):
{rag_context}

Evaluate the student's performance fairly and provide constructive feedback in English.
Skill deltas must be integers between -2 and +2 (0 means no change).

LEVEL READINESS SCORING GUIDE:
- next_level_readiness (0.0–1.0): Evidence the student is ready for the NEXT CEFR level.
  • A1 student → A2: Uses multi-word phrases, basic connectors (and/but/because), simple past attempts.
  • A2 student → B1: Produces short paragraphs, explains reasons, handles past/present/future.
  • B1 student → B2: Uses conditionals (2nd/3rd), passive voice, relative clauses, B2-register vocabulary,
    argues both sides of an abstract topic, hedges opinions ("I think", "It seems").
  • B2 student → C1: Uses inversion, nominalization, precise collocations, sustains complex argument.
  • C1 student → C2: Near-native idiom, register shifts, sophisticated irony/nuance.
  Score 0.0 if student struggles at current level. Score 1.0 only if every answer shows clear next-level mastery.

- structural_complexity (1–5): Syntactic complexity observed across answers.
  1=fragments or isolated words only, 2=simple sentences only,
  3=at least one complex/compound structure used correctly,
  4=consistent use of subordination and varied structures,
  5=embedded clauses, inversion, nominalization, or multiple clause types sustained throughout.

{format_instructions}"""


class EvaluationResult(BaseModel):
    overall_score: float = Field(description="Overall score between 0.0 and 1.0")
    skill_deltas: Dict[str, int] = Field(
        description="Score changes for each skill: grammar, vocabulary, reading, writing. Each value must be -2, -1, 0, 1, or 2."
    )
    feedback: str = Field(description="Constructive feedback in English (2-3 sentences)")
    correct_answers: int = Field(description="Number of correct answers")
    total_questions: int = Field(description="Total number of questions")
    rag_references: List[str] = Field(description="Topics from reference material that were used")
    next_level_readiness: float = Field(
        description="Score 0.0–1.0: readiness for the next CEFR level based on structures and vocabulary observed."
    )
    structural_complexity: int = Field(
        description="1–5: syntactic complexity observed in student answers. See scoring guide."
    )


def evaluator_node(state: GraphState) -> dict:
    """
    Kullanıcının cevaplarını değerlendirir, RAG ile referans materyali kullanır.
    Ajan 4: Değerlendirici
    """
    cefr_level = state.get("cefr_level", "B1")
    daily_content = state.get("daily_content", {})
    messages = state.get("messages", [])

    # Kullanıcının son mesajlarını cevap olarak al
    student_answers = "\n".join(
        f"- {m.content}" for m in messages if hasattr(m, "type") and m.type == "human"
    )
    if not student_answers:
        student_answers = "(No answers provided)"

    # Egzersiz özetini oluştur
    exercises_text = ""
    for i, ex in enumerate(daily_content.get("exercises", []), 1):
        exercises_text += f"{i}. [{ex['type']}] {ex['instruction']}\n   {ex['content']}\n"
        if ex.get("answer"):
            exercises_text += f"   Expected answer: {ex['answer']}\n"

    # RAG: müfredat konusuna göre referans doküman çek
    topic = state.get("daily_curriculum", {}).get("topic", "English grammar")
    rag_docs = search_similar(query=topic, cefr_level=cefr_level, top_k=3)
    rag_context = "\n".join(f"- {doc['content']}" for doc in rag_docs)
    rag_topics = [doc.get("topic", "") for doc in rag_docs]

    parser = PydanticOutputParser(pydantic_object=EvaluationResult)
    prompt = ChatPromptTemplate.from_template(EVALUATOR_SYSTEM_PROMPT)
    chain = prompt | llm | parser

    evaluation = chain.invoke({
        "cefr_level": cefr_level,
        "exercises": exercises_text or "(No exercises)",
        "student_answers": student_answers,
        "rag_context": rag_context or "(No reference material available)",
        "format_instructions": parser.get_format_instructions(),
    })

    # rag_references'ı seed edilen topic isimlerine bağla
    result = evaluation.model_dump()
    result["rag_references"] = rag_topics

    return {"evaluation_result": result}
