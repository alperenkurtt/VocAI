from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from config import OPENROUTER_API_KEY
from state import GraphState

# OpenAI wrapper üzerinden OpenRouter API kullanıyoruz.
llm = ChatOpenAI(
    model="openai/gpt-4o-mini", # OpenRouter'daki herhangi bir modeli seçebiliriz
    openai_api_key=OPENROUTER_API_KEY,
    openai_api_base="https://openrouter.ai/api/v1"
)

def level_detection_node(state: GraphState):
    """
    Kullanıcının cevaplarına bakarak İngilizce CEFR seviyesini tespit eder.
    Ajan 1: Seviye Tespiti (Level Detection)
    """
    messages = state.get("messages", [])
    
    system_prompt = """You are an expert English language teacher and evaluator. 
Your primary goal is to determine the user's English proficiency level on the CEFR scale (A1, A2, B1, B2, C1, C2).
Have a natural conversation with the user by asking them questions. Start with simple questions and gradually increase the difficulty if they answer well.
After asking a maximum of 3-4 questions, if you are confident in their level, you MUST append exactly this string at the very end of your final response: "LEVEL_DETERMINED: [CEFR_LEVEL]".
For example: "LEVEL_DETERMINED: B1"

You can speak in Turkish if necessary to explain something, but strongly encourage the user to reply in English.
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"messages": messages})
    
    content = response.content
    cefr_level = state.get("cefr_level", "")
    assessment_complete = state.get("assessment_complete", False)
    
    if "LEVEL_DETERMINED:" in content:
        # Seviyeyi metinden çıkar
        cefr_level = content.split("LEVEL_DETERMINED:")[1].strip()
        assessment_complete = True
        response.content = f"Harika! İngilizce seviyeni **{cefr_level}** olarak belirledim. Artık senin için müfredat planlayabiliriz."
        
    return {
        "messages": [response], 
        "cefr_level": cefr_level, 
        "assessment_complete": assessment_complete
    }
