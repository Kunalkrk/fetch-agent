"""Unit tests for the parse_retrieve node.

These mock the LLM and the Drive/Gmail connectors so the node's *logic*
(query building, best-effort failure handling, state shape) is verified
without needing live credentials. End-to-end behavior against the real
APIs is exercised separately once ANTHROPIC_API_KEY / Google OAuth /
Slack token are configured.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from src.connectors.drive_client import DriveConnectionError
from src.connectors.gmail_client import GmailConnectionError
from src.nodes.parse_retrieve import ParsedAsk, _build_drive_query, parse_retrieve


def test_build_drive_query_joins_keywords_with_and():
    query = _build_drive_query(["Q4", "Planning"])
    assert query == "title contains 'Q4' and title contains 'Planning'"


def test_build_drive_query_empty_keywords():
    assert _build_drive_query([]) == ""


def test_parse_retrieve_happy_path():
    fake_parsed = ParsedAsk(
        requester="Sarah",
        ask="Q4 Planning Deck",
        deadline="Friday",
        search_keywords=["Q4", "Planning"],
    )

    fake_drive_file = {"id": "abc123", "name": "Q4_Planning_Meeting"}

    with (
        patch("src.nodes.parse_retrieve.ChatAnthropic") as mock_llm_cls,
        patch("src.nodes.parse_retrieve.get_drive_client", new_callable=AsyncMock) as mock_drive,
        patch("src.nodes.parse_retrieve.get_gmail_client", new_callable=AsyncMock) as mock_gmail,
    ):
        mock_structured = AsyncMock()
        mock_structured.ainvoke.return_value = fake_parsed
        mock_llm_cls.return_value.with_structured_output.return_value = mock_structured

        mock_drive_client = AsyncMock()
        mock_drive_client.search_files.return_value = [fake_drive_file]
        mock_drive.return_value = mock_drive_client

        mock_gmail_client = AsyncMock()
        mock_gmail_client.search_messages.return_value = []
        mock_gmail.return_value = mock_gmail_client

        state = {"raw_input": "Sarah asked for the Q4 Planning Deck by Friday - get it done"}
        result = asyncio.run(parse_retrieve(state))

    assert result["ask"] == "Q4 Planning Deck"
    assert result["requester"] == "Sarah"
    assert result["deadline"] == "Friday"
    assert result["source_doc_id"] == "abc123"
    assert result["context_snippets"] == [{"source": "drive", "file": fake_drive_file}]
    assert result["errors"] == []


def test_parse_retrieve_records_drive_failure_without_crashing():
    fake_parsed = ParsedAsk(
        requester="Sarah", ask="Q4 Planning Deck", deadline="Friday", search_keywords=["Q4"]
    )

    with (
        patch("src.nodes.parse_retrieve.ChatAnthropic") as mock_llm_cls,
        patch("src.nodes.parse_retrieve.get_drive_client", new_callable=AsyncMock) as mock_drive,
        patch("src.nodes.parse_retrieve.get_gmail_client", new_callable=AsyncMock) as mock_gmail,
    ):
        mock_structured = AsyncMock()
        mock_structured.ainvoke.return_value = fake_parsed
        mock_llm_cls.return_value.with_structured_output.return_value = mock_structured

        mock_drive.side_effect = DriveConnectionError("no token")
        mock_gmail.side_effect = GmailConnectionError("no token")

        state = {"raw_input": "Sarah asked for the Q4 Planning Deck by Friday - get it done"}
        result = asyncio.run(parse_retrieve(state))

    assert result["source_doc_id"] is None
    assert result["context_snippets"] == []
    assert any("Drive search failed" in e for e in result["errors"])
    assert any("Gmail search failed" in e for e in result["errors"])
