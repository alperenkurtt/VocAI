from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state import GraphState
from agents.level_agent import level_detection_node
from agents.curriculum_agent import curriculum_planner_node
from agents.content_agent import content_generation_node
from agents.evaluator_agent import evaluator_node
from agents.progress_agent import progress_tracker_node


def _route_after_level(state: GraphState) -> str:
    """Seviye tespiti tamamlandıysa müfredata geç, değilse sorulamaya devam et."""
    if state.get("assessment_complete"):
        return "curriculum_agent"
    return "level_agent"


def build_graph(checkpointer=None):
    """
    5 ajanlı LangGraph pipeline'ını oluşturur ve derler.
    checkpointer: UI için MemorySaver, test için None.
    """
    graph = StateGraph(GraphState)

    graph.add_node("level_agent", level_detection_node)
    graph.add_node("curriculum_agent", curriculum_planner_node)
    graph.add_node("content_agent", content_generation_node)
    graph.add_node("evaluator_agent", evaluator_node)
    graph.add_node("progress_agent", progress_tracker_node)

    graph.set_entry_point("level_agent")

    # Ajan 1 → koşullu döngü (assessment_complete olana kadar)
    graph.add_conditional_edges(
        "level_agent",
        _route_after_level,
        {
            "level_agent": "level_agent",
            "curriculum_agent": "curriculum_agent",
        },
    )

    # Ajan 2 → 3 → 4 → 5 → bitiş
    graph.add_edge("curriculum_agent", "content_agent")
    graph.add_edge("content_agent", "evaluator_agent")
    graph.add_edge("evaluator_agent", "progress_agent")
    graph.add_edge("progress_agent", END)

    return graph.compile(checkpointer=checkpointer)


# UI ve testler bu nesneyi doğrudan import eder
app = build_graph(checkpointer=MemorySaver())
