"""Shared Google OAuth credential loading for the Gmail and Drive clients.

One-time setup (run once, interactively, before using gmail_client/drive_client):

    python -m scripts.google_oauth_setup

That runs the installed-app OAuth flow using GOOGLE_OAUTH_CLIENT_ID/SECRET
(or a downloaded client_secret.json) and writes a refreshable token to
GOOGLE_TOKEN_PATH (default: token.json). Everything after that is silent —
get_google_credentials() just loads and, if needed, refreshes that token.
"""

from __future__ import annotations

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive",
]


class GoogleAuthError(RuntimeError):
    """Raised when valid Google credentials can't be loaded."""


def get_google_credentials() -> Credentials:
    token_path = os.environ.get("GOOGLE_TOKEN_PATH", "token.json")

    if not os.path.exists(token_path):
        raise GoogleAuthError(
            f"No token found at {token_path}. Run "
            "`python -m scripts.google_oauth_setup` once to authorize "
            "Gmail + Drive access and generate it."
        )

    creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    if not creds or not creds.valid:
        raise GoogleAuthError(
            f"Google credentials at {token_path} are invalid or expired "
            "and could not be refreshed. Re-run "
            "`python -m scripts.google_oauth_setup`."
        )

    return creds
