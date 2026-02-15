"""Scryfall oracle tag fetcher with local caching."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

RELEVANT_TAGS = [
    "removal",
    "board-wipe",
    "counterspell",
    "bounce",
    "ramp",
    "mana-dork",
    "card-advantage",
    "draw",
    "sacrifice-outlet",
    "recursion",
    "flicker",
    "blink",
    "evasion",
    "burn",
    "tutor",
    "lifegain",
    "discard-outlet",
    "landfall",
    "token-maker",
]

SCRYFALL_SEARCH_URL = "https://api.scryfall.com/cards/search"
USER_AGENT = "cube-utils/0.1.0"
RATE_LIMIT_DELAY = 0.1  # 100ms between requests

DEFAULT_CACHE_PATH = Path("scryfall-tags-cache.json")


def _fetch_tag_oracle_ids(tag: str, session: requests.Session) -> list[str]:
    """Fetch all oracle_ids for cards matching a given Scryfall oracle tag.

    Paginates through all results using has_more / next_page.

    Args:
        tag: The Scryfall oracle tag (e.g. "removal").
        session: A requests.Session with appropriate headers.

    Returns:
        List of oracle_id strings for all matching cards.
    """
    oracle_ids: list[str] = []
    url = SCRYFALL_SEARCH_URL
    params = {"q": f"otag:{tag}", "unique": "cards"}

    while True:
        time.sleep(RATE_LIMIT_DELAY)
        resp = session.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        for card in data.get("data", []):
            oid = card.get("oracle_id", "")
            if oid:
                oracle_ids.append(oid)

        if data.get("has_more") and data.get("next_page"):
            url = data["next_page"]
            params = None  # next_page is a full URL with params
        else:
            break

    return oracle_ids


def fetch_tags(
    tags: list[str] | None = None,
    cache_path: Path | None = None,
) -> dict:
    """Fetch oracle tags from Scryfall and save to a local cache file.

    Args:
        tags: List of oracle tags to fetch. Defaults to RELEVANT_TAGS.
        cache_path: Path to write the cache file. Defaults to DEFAULT_CACHE_PATH.

    Returns:
        The cache dict with 'fetched_at' and 'tags' keys.
    """
    if tags is None:
        tags = RELEVANT_TAGS
    if cache_path is None:
        cache_path = DEFAULT_CACHE_PATH

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    result_tags: dict[str, list[str]] = {}
    for tag in tags:
        oracle_ids = _fetch_tag_oracle_ids(tag, session)
        result_tags[tag] = oracle_ids

    cache = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "tags": result_tags,
    }

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")

    return cache


def load_tags(cache_path: Path | None = None) -> dict[str, list[str]]:
    """Load oracle tags from a local cache file.

    Args:
        cache_path: Path to the cache file. Defaults to DEFAULT_CACHE_PATH.

    Returns:
        Dict mapping tag name to list of oracle_ids.

    Raises:
        FileNotFoundError: If cache file does not exist.
    """
    if cache_path is None:
        cache_path = DEFAULT_CACHE_PATH

    with open(cache_path, encoding="utf-8") as f:
        cache = json.load(f)

    return cache.get("tags", {})
