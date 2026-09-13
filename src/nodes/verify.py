"""Block 4: lightweight LLM-as-judge verification pass.

Reviews the draft against the original ask and produces a pass/fail +
confidence score + notes. This is the reliability signal surfaced in the
final report.
"""

from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

from src.state import AgentState


class VerificationResult(BaseModel):
    passed: bool = Field(description="Does the draft reasonably address the ask?")
    confidence: float = Field(description="0.0-1.0 confidence in this verdict.")
    notes: str = Field(description="1-2 sentence justification, including any concerns.")


_VERIFY_PROMPT = """You are a QA reviewer checking an AI agent's work before it reports \
success to a human.

Original ask: {ask}
Requester: {requester}
Deadline: {deadline}

Drafted deliverable:
---
{draft_content}
---

Errors encountered during the run (if any): {errors}

Judge whether this draft reasonably addresses the ask. A draft that honestly \
flags missing source material and asks clarifying questions (rather than \
inventing content) should still PASS if it's an appropriate, well-structured \
response to a thin/absent source — that is the correct, safe behavior, not a \
failure. Fail only if the draft is off-topic, fabricates specifics it \
couldn't have known, or is otherwise unusable."""


async def verify(state: AgentState) -> AgentState:
    llm = ChatAnthropic(model="claude-sonnet-5")
    structured_llm = llm.with_structured_output(VerificationResult)

    result: VerificationResult = await structured_llm.ainvoke(
        _VERIFY_PROMPT.format(
            ask=state.get("ask"),
            requester=state.get("requester"),
            deadline=state.get("deadline"),
            draft_content=state.get("draft_content") or "(no draft produced)",
            errors=state.get("errors") or "(none)",
        )
    )

    return {
        **state,
        "verification_pass": result.passed,
        "confidence": result.confidence,
        "verification_notes": result.notes,
    }
