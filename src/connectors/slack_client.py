"""Slack connector, backed by the official slack_sdk Web API client."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient


class SlackConnectionError(RuntimeError):
    """Raised when the Slack client can't be constructed or reach Slack."""


@dataclass
class SlackClient:
    client: AsyncWebClient

    async def post_message(self, channel: str, text: str) -> dict[str, Any]:
        """Post a status/report message to a channel."""
        try:
            resp = await self.client.chat_postMessage(channel=channel, text=text)
            return resp.data
        except SlackApiError as e:
            raise SlackConnectionError(f"Failed to post message: {e}") from e

    async def fetch_thread(self, channel: str, thread_ts: str) -> list[dict[str, Any]]:
        """Fetch messages in a thread for context retrieval."""
        try:
            resp = await self.client.conversations_replies(channel=channel, ts=thread_ts)
            return resp.data.get("messages", [])
        except SlackApiError as e:
            raise SlackConnectionError(f"Failed to fetch thread: {e}") from e

    async def read_channel(self, channel: str, limit: int = 20) -> list[dict[str, Any]]:
        """Read recent messages from a channel (used to pick up the trigger)."""
        try:
            resp = await self.client.conversations_history(channel=channel, limit=limit)
            return resp.data.get("messages", [])
        except SlackApiError as e:
            raise SlackConnectionError(f"Failed to read channel: {e}") from e

    async def ping(self) -> bool:
        """Lightweight auth check used by scripts/check_connections.py."""
        try:
            resp = await self.client.auth_test()
            return bool(resp.data.get("ok"))
        except SlackApiError as e:
            raise SlackConnectionError(f"Auth check failed: {e}") from e


async def get_slack_client() -> SlackClient:
    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    if not bot_token:
        raise SlackConnectionError(
            "Missing SLACK_BOT_TOKEN. Create a Slack app, install it to your "
            "workspace, and set the bot token in .env."
        )
    client = SlackClient(client=AsyncWebClient(token=bot_token))
    await client.ping()
    return client
