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

{format_instructions}"""


class Exercise(BaseModel):
    type: str = Field(description="One of: fill_in_blank, multiple_choice, translation, writing_prompt")
    instruction: str = Field(description="Clear instruction for the student")
    content: str = Field(description="The exercise text, question, or prompt")
    answer: Optional[str] = Field(default=None, description="Correct answer (required for fill_in_blank and multiple_choice)")


class DailyContent(BaseModel):
    reading_text: str = Field(description="A reading passage appropriate for the CEFR level (150-250 words)")
    vocabulary_list: List[str] = Field(description="10-12 key vocabulary items, each formatted as 'word: definition'")
    exercises: List[Exercise] = Field(description="5-7 exercises covering the focus skills. Must include at least one writing_prompt exercise that asks the student to write 3-5 sentences.")
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
