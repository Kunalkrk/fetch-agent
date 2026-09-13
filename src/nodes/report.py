"""Block 5: report status back to Slack."""

from __future__ import annotations

import os

from src.connectors.slack_client import SlackConnectionError, get_slack_client
from src.state import AgentState


def _format_report(state: AgentState) -> str:
    status = "✅ Done" if state.get("verification_pass") else "⚠️ Needs review"
    confidence = state.get("confidence")
    confidence_pct = f"{confidence * 100:.0f}%" if confidence is not None else "n/a"

    lines = [
        f"*{status}* — {state.get('ask', 'the ask')} (confidence: {confidence_pct})",
        f"For: {state.get('requester', 'unknown')} · Deadline: {state.get('deadline', 'unspecified')}",
    ]

    if state.get("verification_notes"):
        lines.append(f"_{state['verification_notes']}_")

    if state.get("output_doc_id"):
        lines.append(
            f"Draft: https://docs.google.com/document/d/{state['output_doc_id']}/edit"
        )

    errors = state.get("errors") or []
    if errors:
        lines.append("Issues encountered:")
        lines.extend(f"• {e}" for e in errors)

    return "\n".join(lines)


async def report(state: AgentState) -> AgentState:
    message = _format_report(state)
    report_sent = False

    try:
        slack = await get_slack_client()
        channel = os.environ.get("SLACK_REPORT_CHANNEL")
        if channel:
            await slack.post_message(channel=channel, text=message)
            report_sent = True
    except SlackConnectionError:
        pass

    return {
        **state,
        "report_sent": report_sent,
        "report_message": message,
    }
