"""Google Drive connector.

Used for both retrieval (pulling source data/decks) and output (creating
the drafted deliverable). Swap internals for the real MCP client once the
Drive MCP server is authorized.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional


class DriveConnectionError(RuntimeError):
    """Raised when the Drive client can't be constructed or reach Drive."""


@dataclass
class DriveClient:
    server_url: str

    async def search_files(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Search Drive for files matching a query (name, content, folder)."""
        raise NotImplementedError("Wire up to Drive MCP server / API")

    async def get_file_content(self, file_id: str) -> str:
        """Fetch text/exported content of a file for use as source material."""
        raise NotImplementedError("Wire up to Drive MCP server / API")

    async def create_file(
        self, name: str, content: str, folder_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Create the drafted deliverable as a new Drive file."""
        raise NotImplementedError("Wire up to Drive MCP server / API")

    async def ping(self) -> bool:
        """Lightweight auth check used by scripts/check_connections.py."""
        raise NotImplementedError("Wire up to Drive MCP server / API")


async def get_drive_client() -> DriveClient:
    server_url = os.environ.get("DRIVE_MCP_SERVER_URL")
    if not server_url:
        raise DriveConnectionError(
            "Missing DRIVE_MCP_SERVER_URL. Authorize the Google Drive MCP "
            "connector and set this in .env."
        )
    client = DriveClient(server_url=server_url)
    await client.ping()
    return client
