"""Block 2: parse the triggering ask and retrieve supporting context.

Two steps:
1. An LLM extracts the requester, the ask, the deadline, and a handful of
   search keywords from the raw trigger text (e.g. a Slack message).
2. Those keywords are used to search Google Drive for the source file, and
   (best-effort) Gmail for related context. Retrieval failures don't kill
   the pipeline — they're recorded in state["errors"] so verify/report can
   surface them, and the node continues with whatever it found.
"""

from __future__ import annotations

from typing import Optional

from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

from src.connectors.drive_client import DriveConnectionError, get_drive_client
from src.connectors.gmail_client import GmailConnectionError, get_gmail_client
from src.state import AgentState


class ParsedAsk(BaseModel):
    """Structured extraction of the triggering ask."""

    requester: Optional[str] = Field(
        default=None, description="Who is asking, e.g. 'Sarah'. Null if not named."
    )
    ask: str = Field(description="What deliverable is being asked for, e.g. 'Q4 Planning Deck'.")
    deadline: Optional[str] = Field(
        default=None, description="The deadline as stated, e.g. 'Friday'. Null if not given."
    )
    search_keywords: list[str] = Field(
        description=(
            "2-4 short keywords to search for the source file in Drive/Gmail "
            "(e.g. ['Q4', 'Planning']). Prefer distinctive words from the ask, "
            "skip generic words like 'deck' or 'document'."
        )
    )


_EXTRACTION_PROMPT = """You are parsing a triggering message for an ops agent. \
Extract who asked, what they're asking for, the deadline, and search keywords \
that would help find the source file for it in Google Drive.

Message: {raw_input}"""


def _build_drive_query(keywords: list[str]) -> str:
    clauses = [f"title contains '{kw}'" for kw in keywords if kw]
    return " and ".join(clauses) if clauses else ""


async def parse_retrieve(state: AgentState) -> AgentState:
    errors = list(state.get("errors", []))
    raw_input = state["raw_input"]

    # --- 1. LLM extraction ---
    llm = ChatAnthropic(model="claude-sonnet-5")
    structured_llm = llm.with_structured_output(ParsedAsk)
    parsed: ParsedAsk = await structured_llm.ainvoke(
        _EXTRACTION_PROMPT.format(raw_input=raw_input)
    )

    # --- 2. Drive retrieval (best-effort) ---
    context_snippets: list[dict] = []
    source_doc_id: Optional[str] = None

    try:
        drive = await get_drive_client()
        query = _build_drive_query(parsed.search_keywords)
        matches = await drive.search_files(query, max_results=5) if query else []
        if matches:
            source_doc_id = matches[0]["id"]
            context_snippets.append({"source": "drive", "file": matches[0]})
    except DriveConnectionError as e:
        errors.append(f"parse_retrieve: Drive search failed: {e}")

    # --- 3. Gmail context (best-effort) ---
    try:
        gmail = await get_gmail_client()
        gmail_query = " ".join(parsed.search_keywords)
        messages = await gmail.search_messages(gmail_query, max_results=3) if gmail_query else []
        for m in messages:
            context_snippets.append({"source": "gmail", "message": m})
    except GmailConnectionError as e:
        errors.append(f"parse_retrieve: Gmail search failed: {e}")

    return {
        **state,
        "ask": parsed.ask,
        "requester": parsed.requester,
        "deadline": parsed.deadline,
        "context_snippets": context_snippets,
        "source_doc_id": source_doc_id,
        "errors": errors,
    }
