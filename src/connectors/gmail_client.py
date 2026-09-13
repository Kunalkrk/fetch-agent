"""Gmail connector.

Thin wrapper used for context retrieval (finding the thread the ask came
from, or related emails referenced by it). Swap internals for the real
MCP client once the Gmail MCP server is authorized.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


class GmailConnectionError(RuntimeError):
    """Raised when the Gmail client can't be constructed or reach Gmail."""


@dataclass
class GmailClient:
    server_url: str

    async def search_messages(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Search for messages matching a query string (sender, subject, keywords)."""
        raise NotImplementedError("Wire up to Gmail MCP server / API")

    async def get_thread(self, thread_id: str) -> dict[str, Any]:
        """Fetch a full thread for context."""
        raise NotImplementedError("Wire up to Gmail MCP server / API")

    async def ping(self) -> bool:
        """Lightweight auth check used by scripts/check_connections.py."""
        raise NotImplementedError("Wire up to Gmail MCP server / API")


async def get_gmail_client() -> GmailClient:
    server_url = os.environ.get("GMAIL_MCP_SERVER_URL")
    if not server_url:
        raise GmailConnectionError(
            "Missing GMAIL_MCP_SERVER_URL. Authorize the Gmail MCP connector "
            "and set this in .env."
        )
    client = GmailClient(server_url=server_url)
    await client.ping()
    return client
