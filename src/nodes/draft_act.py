"""Block 3: draft the deliverable and take the follow-up action.

Fetches the source file's content (if one was found in parse_retrieve),
has the LLM draft a structured outline for the requested deliverable, and
creates that draft as a new Google Doc in Drive.
"""

from __future__ import annotations

import os

from langchain_anthropic import ChatAnthropic

from src.connectors.drive_client import DriveConnectionError, get_drive_client
from src.state import AgentState

_DRAFT_PROMPT = """You are an ops assistant drafting a deliverable on someone's behalf.

Requester: {requester}
Ask: {ask}
Deadline: {deadline}

Source material (may be empty if none was found):
---
{source_content}
---

Write a clear, well-structured outline/draft for the requested deliverable, \
grounded in the source material where possible. Use markdown-style headers \
and bullet points. If the source material is empty or insufficient, say so \
explicitly at the top rather than inventing content."""


def _find_source_doc(state: AgentState) -> tuple[str | None, str | None]:
    """Return (file_id, file_name) for the first Drive snippet, if any."""
    for snippet in state.get("context_snippets", []):
        if snippet.get("source") == "drive":
            file = snippet["file"]
            return file["id"], file.get("name")
    return None, None


async def draft_act(state: AgentState) -> AgentState:
    errors = list(state.get("errors", []))
    ask = state.get("ask", "the requested deliverable")
    requester = state.get("requester") or "someone"
    deadline = state.get("deadline") or "no stated deadline"

    source_doc_id, source_name = _find_source_doc(state)
    source_content = ""

    drive = None
    try:
        drive = await get_drive_client()
        if source_doc_id:
            source_content = await drive.get_file_content(source_doc_id)
    except DriveConnectionError as e:
        errors.append(f"draft_act: Drive access failed: {e}")

    # --- Draft the deliverable ---
    llm = ChatAnthropic(model="claude-sonnet-5")
    draft_response = await llm.ainvoke(
        _DRAFT_PROMPT.format(
            requester=requester,
            ask=ask,
            deadline=deadline,
            source_content=source_content or "(no source material found)",
        )
    )
    draft_content = draft_response.content

    # --- Create the follow-up artifact in Drive ---
    output_doc_id = None
    if drive is not None:
        try:
            output_name = f"{ask} - Draft"
            result = await drive.create_file(
                name=output_name,
                content=draft_content,
                folder_id=os.environ.get("DRIVE_OUTPUT_FOLDER_ID") or None,
            )
            output_doc_id = result["id"]
        except DriveConnectionError as e:
            errors.append(f"draft_act: Failed to create output file: {e}")

    return {
        **state,
        "draft_content": draft_content,
        "output_doc_id": output_doc_id,
        "errors": errors,
    }
