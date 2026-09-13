"""Block 2: parse the triggering ask and retrieve supporting context.

TODO (Block 2):
- Extract `ask`, `requester`, `deadline` from state["raw_input"] (LLM call).
- Use gmail_client.search_messages / drive_client.search_files to pull
  relevant context_snippets and a source_doc_id.
- Keep the first pass narrow: it's fine to hardcode the test-case query.
"""

from __future__ import annotations

from src.state import AgentState


async def parse_retrieve(state: AgentState) -> AgentState:
    raise NotImplementedError("Block 2: implement parse + retrieve")
