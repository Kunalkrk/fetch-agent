"""Block 4: lightweight LLM-as-judge verification pass.

TODO (Block 4):
- Have an LLM review draft_content against the original ask + deadline
  and produce a pass/fail + confidence score (0.0-1.0) + short notes.
- Write verification_pass, confidence, verification_notes into state.
- This is the reliability signal surfaced in the final report — don't
  let a failing check get silently reported as success downstream.
"""

from __future__ import annotations

from src.state import AgentState


async def verify(state: AgentState) -> AgentState:
    raise NotImplementedError("Block 4: implement verification pass")
