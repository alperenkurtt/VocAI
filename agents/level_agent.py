import re
from langchain_core.prompts import ChatPromptTemplate
from config import llm
from state import GraphState

system_prompt = """You are an expert English language assessor using the CEFR framework.

CEFR CRITERIA:
- A1: Only knows basic phrases ("hello", "my name is"). Cannot form sentences independently.
- A2: Uses simple past/present tense. Makes frequent grammar errors but is understandable.
- B1: Can express opinions on familiar topics. Errors don't block understanding.
- B2: Handles abstract topics, uses complex sentences, occasional errors only.
- C1: Fluent and flexible, precise vocabulary, rare errors.
- C2: Near-native. Uses nuance, idioms, and academic register naturally.

ASSESSMENT RULES:
1. Ask exactly 6-8 questions. Start simple, increase difficulty based on responses.
2. Ask ONE question at a time. Wait for the answer before proceeding.
3. Vary question types: describe a situation, explain a concept, give an opinion, tell a story.
4. Internally track: grammar accuracy, vocabulary range, sentence complexity, coherence.
5. Do NOT determine the level before the 5th answer.
6. After at least 5 answers, when confident, append EXACTLY this at the end of your response:
   LEVEL_DETERMINED: [LEVEL]
   Example: LEVEL_DETERMINED: B1

You can use Turkish only to give brief instructions at the very start. All questions must be in English.
"""

def level_detection_node(state: GraphState):
    """
    Kullanıcının cevaplarına bakarak İngilizce CEFR seviyesini tespit eder.
    Ajan 1: Seviye Tespiti (Level Detection)
    """
    messages = state.get("messages", [])

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}")
    ])

    chain = prompt | llm
    response = chain.invoke({"messages": messages})

    content = response.content
    cefr_level = state.get("cefr_level", "")
    assessment_complete = state.get("assessment_complete", False)

    match = re.search(r"LEVEL_DETERMINED:\s*(A1|A2|B1|B2|C1|C2)", content)
    if match:
        cefr_level = match.group(1)
        assessment_complete = True
        # LEVEL_DETERMINED tag'ini kullanıcıya gösterme
        clean_content = re.sub(r"\s*LEVEL_DETERMINED:\s*(A1|A2|B1|B2|C1|C2)", "", content).strip()
        response.content = f"{clean_content}\n\n---\nHarika! İngilizce seviyeni **{cefr_level}** olarak belirledim. Artık senin için müfredat planlayabiliriz."

    return {
        "messages": [response],
        "cefr_level": cefr_level,
        "assessment_complete": assessment_complete
    }
