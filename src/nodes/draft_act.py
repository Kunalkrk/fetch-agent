"""Block 3: draft the deliverable and take the follow-up action.

TODO (Block 3):
- Generate `draft_content` from state["ask"] + state["context_snippets"]
  (LLM call).
- Create the artifact via drive_client.create_file (doc draft) and/or a
  calendar block / task. Keep the output format simple for the MVP.
"""

from __future__ import annotations

from src.state import AgentState


async def draft_act(state: AgentState) -> AgentState:
    raise NotImplementedError("Block 3: implement draft + act")
