"""Block 5: report status back to Slack.

TODO (Block 5):
- Compose a status message including the confidence/pass-fail signal
  from the verify node and links to whatever was created (doc/task/event).
- Post it via slack_client.post_message to SLACK_REPORT_CHANNEL.
- Set report_sent / report_message in state.
"""

from __future__ import annotations

from src.state import AgentState


async def report(state: AgentState) -> AgentState:
    raise NotImplementedError("Block 5: implement Slack report-back")
