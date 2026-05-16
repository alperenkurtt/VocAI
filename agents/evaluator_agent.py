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

Evaluate the student's performance fairly and provide constructive feedback in Turkish.
Skill deltas must be integers between -2 and +2 (0 means no change).

{format_instructions}"""


class EvaluationResult(BaseModel):
    overall_score: float = Field(description="Overall score between 0.0 and 1.0")
    skill_deltas: Dict[str, int] = Field(
        description="Score changes for each skill: grammar, vocabulary, reading, writing. Each value must be -2, -1, 0, 1, or 2."
    )
    feedback: str = Field(description="Constructive feedback in Turkish (2-3 sentences)")
    correct_answers: int = Field(description="Number of correct answers")
    total_questions: int = Field(description="Total number of questions")
    rag_references: List[str] = Field(description="Topics from reference material that were used")


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
    topic = daily_content.get("grammar_note", "English grammar")
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
