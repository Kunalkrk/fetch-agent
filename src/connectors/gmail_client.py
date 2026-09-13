"""Gmail connector, backed by the Google API Python client.

Used for context retrieval (finding the thread the ask came from, or
related emails referenced by it). Auth: see google_auth.py /
scripts/google_oauth_setup.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.connectors.google_auth import GoogleAuthError, get_google_credentials


class GmailConnectionError(RuntimeError):
    """Raised when the Gmail client can't be constructed or reach Gmail."""


@dataclass
class GmailClient:
    service: Any  # googleapiclient Resource

    async def search_messages(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Search for messages matching a Gmail search query (e.g. 'from:sarah subject:Q4')."""
        try:
            resp = (
                self.service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )
            return resp.get("messages", [])
        except HttpError as e:
            raise GmailConnectionError(f"Failed to search messages: {e}") from e

    async def get_thread(self, thread_id: str) -> dict[str, Any]:
        """Fetch a full thread for context."""
        try:
            return (
                self.service.users()
                .threads()
                .get(userId="me", id=thread_id, format="full")
                .execute()
            )
        except HttpError as e:
            raise GmailConnectionError(f"Failed to fetch thread {thread_id}: {e}") from e

    async def ping(self) -> bool:
        """Lightweight auth check used by scripts/check_connections.py."""
        try:
            self.service.users().getProfile(userId="me").execute()
            return True
        except HttpError as e:
            raise GmailConnectionError(f"Auth check failed: {e}") from e


async def get_gmail_client() -> GmailClient:
    try:
        creds = get_google_credentials()
    except GoogleAuthError as e:
        raise GmailConnectionError(str(e)) from e
    service = build("gmail", "v1", credentials=creds)
    client = GmailClient(service=service)
    await client.ping()
    return client
