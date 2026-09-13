"""Shared state schema threaded through the Fetch LangGraph pipeline."""

from __future__ import annotations

from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    # --- input ---
    raw_input: str                  # the triggering Slack message / email text
    source: str                     # "slack" | "gmail" | "cli"

    # --- parse_retrieve node ---
    ask: str                        # extracted task description
    requester: Optional[str]        # who asked ("Sarah")
    deadline: Optional[str]         # extracted deadline, ISO-ish or free text
    context_snippets: list[dict[str, Any]]  # retrieved Gmail/Drive context
    source_doc_id: Optional[str]    # Drive file id used as source material

    # --- draft_act node ---
    draft_content: Optional[str]    # generated deliverable content/outline
    output_doc_id: Optional[str]    # Drive file id created for the draft
    calendar_event_id: Optional[str]
    task_id: Optional[str]

    # --- verify node ---
    verification_pass: Optional[bool]
    confidence: Optional[float]     # 0.0 - 1.0
    verification_notes: Optional[str]

    # --- report node ---
    report_sent: Optional[bool]
    report_message: Optional[str]

    # --- bookkeeping ---
    errors: list[str]
