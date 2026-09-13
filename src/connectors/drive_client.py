"""Google Drive connector, backed by the Google API Python client.

Used for both retrieval (pulling source data/decks) and output (creating
the drafted deliverable). Auth: see google_auth.py /
scripts/google_oauth_setup.py.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from src.connectors.google_auth import GoogleAuthError, get_google_credentials

# Google-native types must be *exported* to a real format, not downloaded raw.
_EXPORT_MIME_TYPES = {
    "application/vnd.google-apps.document": "text/plain",
    "application/vnd.google-apps.presentation": "text/plain",
    "application/vnd.google-apps.spreadsheet": "text/csv",
}


class DriveConnectionError(RuntimeError):
    """Raised when the Drive client can't be constructed or reach Drive."""


@dataclass
class DriveClient:
    service: Any  # googleapiclient Resource

    async def search_files(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Search Drive using a raw Drive v3 query string, e.g. `name contains 'Q4'`."""
        try:
            resp = (
                self.service.files()
                .list(
                    q=query,
                    pageSize=max_results,
                    fields="files(id, name, mimeType, modifiedTime, webViewLink)",
                )
                .execute()
            )
            return resp.get("files", [])
        except HttpError as e:
            raise DriveConnectionError(f"Failed to search files: {e}") from e

    async def get_file_content(self, file_id: str) -> str:
        """Fetch text content of a file (exporting Google-native docs/slides/sheets as needed)."""
        try:
            metadata = self.service.files().get(fileId=file_id, fields="mimeType").execute()
            mime_type = metadata["mimeType"]

            if mime_type in _EXPORT_MIME_TYPES:
                request = self.service.files().export_media(
                    fileId=file_id, mimeType=_EXPORT_MIME_TYPES[mime_type]
                )
            else:
                request = self.service.files().get_media(fileId=file_id)

            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

            return buffer.getvalue().decode("utf-8", errors="replace")
        except HttpError as e:
            raise DriveConnectionError(f"Failed to fetch content for {file_id}: {e}") from e

    async def create_file(
        self, name: str, content: str, folder_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Create the drafted deliverable as a new Drive file (plain text/Google Doc)."""
        try:
            file_metadata: dict[str, Any] = {"name": name}
            if folder_id:
                file_metadata["parents"] = [folder_id]

            media = MediaIoBaseUpload(
                io.BytesIO(content.encode("utf-8")), mimetype="text/plain", resumable=False
            )
            return (
                self.service.files()
                .create(body=file_metadata, media_body=media, fields="id, name, webViewLink")
                .execute()
            )
        except HttpError as e:
            raise DriveConnectionError(f"Failed to create file {name}: {e}") from e

    async def ping(self) -> bool:
        """Lightweight auth check used by scripts/check_connections.py."""
        try:
            self.service.about().get(fields="user").execute()
            return True
        except HttpError as e:
            raise DriveConnectionError(f"Auth check failed: {e}") from e


async def get_drive_client() -> DriveClient:
    try:
        creds = get_google_credentials()
    except GoogleAuthError as e:
        raise DriveConnectionError(str(e)) from e
    service = build("drive", "v3", credentials=creds)
    client = DriveClient(service=service)
    await client.ping()
    return client
