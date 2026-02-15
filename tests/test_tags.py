"""Tests for Scryfall oracle tag fetcher."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from cube_utils.tags import (
    DEFAULT_CACHE_PATH,
    RELEVANT_TAGS,
    _fetch_tag_oracle_ids,
    fetch_tags,
    load_tags,
)


class TestFetchTagOracleIds:
    """Tests for _fetch_tag_oracle_ids (single tag fetch)."""

    def test_single_page(self):
        session = MagicMock()
        response = MagicMock()
        response.json.return_value = {
            "data": [
                {"oracle_id": "oid-1", "name": "Card A"},
                {"oracle_id": "oid-2", "name": "Card B"},
            ],
            "has_more": False,
        }
        session.get.return_value = response

        result = _fetch_tag_oracle_ids("removal", session)
        assert result == ["oid-1", "oid-2"]
        session.get.assert_called_once()

    def test_pagination(self):
        session = MagicMock()
        page1 = MagicMock()
        page1.json.return_value = {
            "data": [{"oracle_id": "oid-1"}],
            "has_more": True,
            "next_page": "https://api.scryfall.com/cards/search?page=2",
        }
        page2 = MagicMock()
        page2.json.return_value = {
            "data": [{"oracle_id": "oid-2"}],
            "has_more": False,
        }
        session.get.side_effect = [page1, page2]

        result = _fetch_tag_oracle_ids("removal", session)
        assert result == ["oid-1", "oid-2"]
        assert session.get.call_count == 2

    def test_skips_cards_without_oracle_id(self):
        session = MagicMock()
        response = MagicMock()
        response.json.return_value = {
            "data": [
                {"oracle_id": "oid-1"},
                {"name": "No Oracle ID"},
                {"oracle_id": "", "name": "Empty Oracle ID"},
            ],
            "has_more": False,
        }
        session.get.return_value = response

        result = _fetch_tag_oracle_ids("removal", session)
        assert result == ["oid-1"]


class TestFetchTags:
    """Tests for fetch_tags (full fetch + cache write)."""

    @patch("cube_utils.tags._fetch_tag_oracle_ids")
    @patch("cube_utils.tags.requests.Session")
    def test_writes_cache_file(self, mock_session_cls, mock_fetch, tmp_path):
        mock_fetch.return_value = ["oid-1", "oid-2"]
        cache_path = tmp_path / "cache.json"

        result = fetch_tags(tags=["removal", "ramp"], cache_path=cache_path)

        assert cache_path.exists()
        data = json.loads(cache_path.read_text())
        assert "fetched_at" in data
        assert "removal" in data["tags"]
        assert "ramp" in data["tags"]
        assert data["tags"]["removal"] == ["oid-1", "oid-2"]

    @patch("cube_utils.tags._fetch_tag_oracle_ids")
    @patch("cube_utils.tags.requests.Session")
    def test_returns_cache_dict(self, mock_session_cls, mock_fetch, tmp_path):
        mock_fetch.return_value = ["oid-1"]
        cache_path = tmp_path / "cache.json"

        result = fetch_tags(tags=["removal"], cache_path=cache_path)

        assert "fetched_at" in result
        assert result["tags"]["removal"] == ["oid-1"]

    @patch("cube_utils.tags._fetch_tag_oracle_ids")
    @patch("cube_utils.tags.requests.Session")
    def test_calls_fetch_for_each_tag(self, mock_session_cls, mock_fetch, tmp_path):
        mock_fetch.return_value = []
        cache_path = tmp_path / "cache.json"
        tags = ["removal", "ramp", "evasion"]

        fetch_tags(tags=tags, cache_path=cache_path)

        assert mock_fetch.call_count == 3


class TestLoadTags:
    """Tests for load_tags (cache loading)."""

    def test_loads_from_cache(self, tmp_path):
        cache_path = tmp_path / "cache.json"
        cache_data = {
            "fetched_at": "2026-02-14T00:00:00+00:00",
            "tags": {
                "removal": ["oid-1", "oid-2"],
                "ramp": ["oid-3"],
            },
        }
        cache_path.write_text(json.dumps(cache_data))

        result = load_tags(cache_path)
        assert result == {"removal": ["oid-1", "oid-2"], "ramp": ["oid-3"]}

    def test_raises_if_no_cache(self, tmp_path):
        cache_path = tmp_path / "nonexistent.json"
        import pytest

        with pytest.raises(FileNotFoundError):
            load_tags(cache_path)

    def test_returns_empty_if_no_tags_key(self, tmp_path):
        cache_path = tmp_path / "cache.json"
        cache_path.write_text(json.dumps({"fetched_at": "2026-01-01"}))

        result = load_tags(cache_path)
        assert result == {}
