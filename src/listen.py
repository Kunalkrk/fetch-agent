"""Live Slack listener: runs Fetch automatically when a new message arrives
in SLACK_REPORT_CHANNEL, via Slack Socket Mode.

Usage:
    python -m src.listen

Requires SLACK_APP_TOKEN (xapp-...) in addition to SLACK_BOT_TOKEN.
"""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.web.async_client import AsyncWebClient

from src.graph import build_graph

_seen_ts: set[str] = set()


async def handle_request(client: SocketModeClient, req: SocketModeRequest) -> None:
    # Ack immediately so Slack doesn't retry.
    await client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))

    if req.type != "events_api":
        return

    event = req.payload.get("event", {})
    if event.get("type") != "message" or event.get("subtype") is not None:
        return  # ignore edits, bot messages, joins, etc.

    if event.get("bot_id"):
        return  # ignore our own / other bots' messages

    channel = event.get("channel")
    report_channel = os.environ.get("SLACK_REPORT_CHANNEL")
    if report_channel and channel != report_channel:
        return

    ts = event.get("ts")
    if ts in _seen_ts:
        return
    _seen_ts.add(ts)

    text = event.get("text", "")
    print(f"🟢 New trigger message: {text!r}")

    graph = build_graph()
    try:
        result = await graph.ainvoke(
            {"raw_input": text, "source": "slack", "errors": []}
        )
        print(f"✅ Pipeline finished. report_sent={result.get('report_sent')}")
    except Exception as e:  # noqa: BLE001 - keep the listener alive on any node failure
        print(f"❌ Pipeline failed: {e}")


async def main() -> None:
    load_dotenv()

    app_token = os.environ.get("SLACK_APP_TOKEN")
    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    if not app_token or not bot_token:
        raise SystemExit("Missing SLACK_APP_TOKEN or SLACK_BOT_TOKEN in .env")

    web_client = AsyncWebClient(token=bot_token)
    client = SocketModeClient(app_token=app_token, web_client=web_client)
    client.socket_mode_request_listeners.append(handle_request)

    print("👂 Fetch listener running. Post a message in the report channel to trigger it...")
    await client.connect()
    await asyncio.Event().wait()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
