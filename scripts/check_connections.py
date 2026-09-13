"""Quick smoke test: confirm Slack, Gmail, and Drive connectors are alive.

Run this first, before building anything else — it's the riskiest failure
point (auth/config issues surface immediately instead of mid-pipeline).

    python scripts/check_connections.py
"""

from __future__ import annotations

import asyncio

from dotenv import load_dotenv

from src.connectors.drive_client import get_drive_client
from src.connectors.gmail_client import get_gmail_client
from src.connectors.slack_client import get_slack_client


async def main() -> None:
    load_dotenv()

    checks = [
        ("Slack", get_slack_client),
        ("Gmail", get_gmail_client),
        ("Drive", get_drive_client),
    ]

    results = []
    for name, getter in checks:
        try:
            await getter()
            print(f"✅ {name} connected")
            results.append(True)
        except Exception as e:  # noqa: BLE001 - smoke test, report every failure
            print(f"❌ {name} failed: {e}")
            results.append(False)

    if not all(results):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
