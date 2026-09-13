"""Slack connector.

Thin wrapper so the rest of the pipeline never talks to Slack's API/MCP
server directly. Swap the internals for the real MCP client once the
Slack MCP server is authorized — the call signatures below (post_message,
fetch_thread) are the contract the nodes rely on.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional


class SlackConnectionError(RuntimeError):
    """Raised when the Slack client can't be constructed or reach Slack."""


@dataclass
class SlackClient:
    server_url: str
    bot_token: str

    async def post_message(self, channel: str, text: str) -> dict[str, Any]:
        """Post a status/report message to a channel."""
        raise NotImplementedError("Wire up to Slack MCP server / Web API")

    async def fetch_thread(self, channel: str, thread_ts: str) -> list[dict[str, Any]]:
        """Fetch messages in a thread for context retrieval."""
        raise NotImplementedError("Wire up to Slack MCP server / Web API")

    async def ping(self) -> bool:
        """Lightweight auth check used by scripts/check_connections.py."""
        raise NotImplementedError("Wire up to Slack MCP server / Web API")


async def get_slack_client() -> SlackClient:
    server_url = os.environ.get("SLACK_MCP_SERVER_URL")
    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    if not server_url or not bot_token:
        raise SlackConnectionError(
            "Missing SLACK_MCP_SERVER_URL or SLACK_BOT_TOKEN. "
            "Authorize the Slack MCP connector and set these in .env."
        )
    client = SlackClient(server_url=server_url, bot_token=bot_token)
    await client.ping()
    return client
