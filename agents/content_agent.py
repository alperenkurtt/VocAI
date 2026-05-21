from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
from config import llm
from state import GraphState

CONTENT_SYSTEM_PROMPT = """You are an expert English language teacher creating a daily lesson.

Student CEFR level: {cefr_level}
Today's topic: {topic}
Theme: {theme}
Skills to practice: {focus_skills}
Objectives: {objectives}

Create engaging, level-appropriate content. Keep language complexity suitable for the CEFR level.

EXERCISE REQUIREMENTS — create EXACTLY 10 exercises in this order:
  1-4:  fill_in_blank   (4 exercises) — one blank per sentence, provide the correct word as answer
  5-8:  multiple_choice (4 exercises) — provide exactly 4 options (A/B/C/D), answer is the correct letter
  9-10: writing_prompt  (2 exercises) — ask the student to write 3-5 sentences on a specific topic

Do NOT create translation exercises.

For multiple_choice exercises, options must be a list of exactly 4 strings, each prefixed with
"A) ", "B) ", "C) ", "D) ". The answer field must be just the letter: "A", "B", "C", or "D".

{format_instructions}"""


class Exercise(BaseModel):
    type: str = Field(description="One of: fill_in_blank, multiple_choice, writing_prompt")
    instruction: str = Field(description="Clear instruction for the student in English")
    content: str = Field(description="The exercise text, sentence with blank, or writing topic")
    answer: Optional[str] = Field(
        default=None,
        description="For fill_in_blank: the correct word. For multiple_choice: just the letter (A/B/C/D). For writing_prompt: null."
    )
    options: Optional[List[str]] = Field(
        default=None,
        description="For multiple_choice only: exactly 4 strings like ['A) option', 'B) option', 'C) option', 'D) option']. Null for other types."
    )


class DailyContent(BaseModel):
    reading_text: str = Field(description="A reading passage appropriate for the CEFR level (150-250 words)")
    vocabulary_list: List[str] = Field(description="10-12 key vocabulary items, each formatted as 'word: definition'")
    exercises: List[Exercise] = Field(description="Exactly 10 exercises: 4 fill_in_blank, 4 multiple_choice, 2 writing_prompt — in that order.")
    grammar_note: str = Field(description="A concise grammar tip relevant to today's topic (2-3 sentences)")


def content_generation_node(state: GraphState) -> dict:
    """
    Ajan 2'nin ürettiği müfredatı alarak gerçek ders içeriği üretir.
    Ajan 3: İçerik Üretici
    """
    cefr_level = state.get("cefr_level", "B1")
    curriculum = state.get("daily_curriculum", {})

    parser = PydanticOutputParser(pydantic_object=DailyContent)
    prompt = ChatPromptTemplate.from_template(CONTENT_SYSTEM_PROMPT)
    chain = prompt | llm | parser

    content = chain.invoke({
        "cefr_level": cefr_level,
        "topic": curriculum.get("topic", "General English"),
        "theme": curriculum.get("theme", "Everyday life"),
        "focus_skills": ", ".join(curriculum.get("focus_skills", ["grammar", "vocabulary"])),
        "objectives": "; ".join(curriculum.get("objectives", ["Improve English skills"])),
        "format_instructions": parser.get_format_instructions(),
    })

    return {"daily_content": content.model_dump()}
