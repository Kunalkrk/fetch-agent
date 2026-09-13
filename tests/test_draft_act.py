"""Unit tests for the draft_act node.

Mocks the LLM and Drive connector so the node's logic (finding the source
doc, drafting, creating the output file, best-effort failure handling) is
verified without live credentials.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.connectors.drive_client import DriveConnectionError
from src.nodes.draft_act import _find_source_doc, draft_act


def test_find_source_doc_returns_first_drive_snippet():
    state = {
        "context_snippets": [
            {"source": "gmail", "message": {"id": "m1"}},
            {"source": "drive", "file": {"id": "d1", "name": "Some Deck"}},
        ]
    }
    file_id, name = _find_source_doc(state)
    assert file_id == "d1"
    assert name == "Some Deck"


def test_find_source_doc_returns_none_when_absent():
    assert _find_source_doc({"context_snippets": []}) == (None, None)


def test_draft_act_happy_path():
    state = {
        "ask": "Q4 Planning Deck",
        "requester": "Sarah",
        "deadline": "Friday",
        "context_snippets": [{"source": "drive", "file": {"id": "src1", "name": "Q4_Planning"}}],
        "errors": [],
    }

    with (
        patch("src.nodes.draft_act.ChatAnthropic") as mock_llm_cls,
        patch("src.nodes.draft_act.get_drive_client", new_callable=AsyncMock) as mock_get_drive,
    ):
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(content="# Q4 Planning Deck\n\n- point one")
        mock_llm_cls.return_value = mock_llm

        mock_drive = AsyncMock()
        mock_drive.get_file_content.return_value = "source deck text"
        mock_drive.create_file.return_value = {"id": "out1", "name": "Q4 Planning Deck - Draft"}
        mock_get_drive.return_value = mock_drive

        result = asyncio.run(draft_act(state))

    mock_drive.get_file_content.assert_awaited_once_with("src1")
    mock_drive.create_file.assert_awaited_once()
    assert result["draft_content"] == "# Q4 Planning Deck\n\n- point one"
    assert result["output_doc_id"] == "out1"
    assert result["errors"] == []


def test_draft_act_records_drive_failure_without_crashing():
    state = {
        "ask": "Q4 Planning Deck",
        "requester": "Sarah",
        "deadline": "Friday",
        "context_snippets": [],
        "errors": [],
    }

    with (
        patch("src.nodes.draft_act.ChatAnthropic") as mock_llm_cls,
        patch("src.nodes.draft_act.get_drive_client", new_callable=AsyncMock) as mock_get_drive,
    ):
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(content="# Draft with no source")
        mock_llm_cls.return_value = mock_llm

        mock_get_drive.side_effect = DriveConnectionError("no token")

        result = asyncio.run(draft_act(state))

    assert result["draft_content"] == "# Draft with no source"
    assert result["output_doc_id"] is None
    assert any("Drive access failed" in e for e in result["errors"])
