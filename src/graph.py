"""LangGraph pipeline definition for Fetch.

trigger -> parse_retrieve -> draft_act -> verify -> report
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.nodes.draft_act import draft_act
from src.nodes.parse_retrieve import parse_retrieve
from src.nodes.report import report
from src.nodes.verify import verify
from src.state import AgentState


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("parse_retrieve", parse_retrieve)
    graph.add_node("draft_act", draft_act)
    graph.add_node("verify", verify)
    graph.add_node("report", report)

    graph.set_entry_point("parse_retrieve")
    graph.add_edge("parse_retrieve", "draft_act")
    graph.add_edge("draft_act", "verify")
    graph.add_edge("verify", "report")
    graph.add_edge("report", END)

    return graph.compile()
