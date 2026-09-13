"""One-time interactive OAuth setup for Gmail + Drive.

Run this once, locally, before using gmail_client/drive_client:

    python -m scripts.google_oauth_setup

It opens a browser for you to grant access, then writes a refreshable
token to GOOGLE_TOKEN_PATH (default: token.json). Requires
GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET in .env (from a
Google Cloud OAuth client of type "Desktop app").
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

from src.connectors.google_auth import SCOPES


def main() -> None:
    load_dotenv()

    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    token_path = os.environ.get("GOOGLE_TOKEN_PATH", "token.json")

    if not client_id or not client_secret:
        raise SystemExit(
            "Missing GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET in .env. "
            "Create a Desktop app OAuth client in Google Cloud Console and set these."
        )

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(token_path, "w") as f:
        f.write(creds.to_json())

    print(f"✅ Google credentials saved to {token_path}")


if __name__ == "__main__":
    main()
