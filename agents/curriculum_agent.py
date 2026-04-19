from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
from config import llm
from state import GraphState

class CurriculumPlan(BaseModel):
    topic: str = Field(description="The main grammar or vocabulary topic (e.g., Present Perfect Tense, Travel Vocabulary)")
    theme: str = Field(description="A fun, engaging context for the lesson (e.g., At the Airport, Technology in the Future)")
    focus_skills: List[str] = Field(description="List of 2-3 skills to practice today, e.g., Grammar, Vocabulary, Reading")
    objectives: List[str] = Field(description="1-2 sentences explaining what the user will achieve today in English")

def curriculum_planner_node(state: GraphState):
    """
    Kullanıcının seviyesini ve zayıf yönlerini (ileride eklenecek) alarak
    günlük bir ders planı JSON'u üretir.
    Ajan 2: Müfredat Planlayıcı (Curriculum Planner)
    """
    cefr_level = state.get("cefr_level", "B1")
    
    parser = PydanticOutputParser(pydantic_object=CurriculumPlan)
    
    system_prompt = """You are an expert English Curriculum Planner. 
The user is at the {cefr_level} proficiency level on the CEFR scale.
Your task is to generate a daily learning module tailored to this level.

{format_instructions}
"""
    prompt = ChatPromptTemplate.from_template(system_prompt)
    
    chain = prompt | llm | parser
    
    curriculum = chain.invoke({
        "cefr_level": cefr_level,
        "format_instructions": parser.get_format_instructions()
    })
    
    return {
        "daily_curriculum": curriculum.model_dump()
    }
