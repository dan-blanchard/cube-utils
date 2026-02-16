"""Shared test fixtures for cube_utils tests."""

import json
import textwrap
from pathlib import Path

import pytest

from cube_utils.cards import Card


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    """Create a sample cube CSV file for testing."""
    csv_path = tmp_path / "cube.csv"
    csv_path.write_text(
        textwrap.dedent("""\
            quantity,card name,color,cmc,scryfall ID,types,card text
            1,Lightning Bolt,"Red",1,e3285e6b-3e79-4d7c-bf96-d920f973b122,"Instant","Lightning Bolt deals 3 damage to any target."
            1,Counterspell,"Blue",2,1920dae4-fb92-4f19-ae4b-eb3276b8571c,"Instant","Counter target spell."
            1,Anax and Cymede,"White,Red",3,71d9fd43-576f-45db-ab8f-a9f2a0427398,"Creature","First strike, vigilance Heroic -- Whenever you cast a spell that targets Anax and Cymede, creatures you control get +1/+1 and gain trample until end of turn."
            1,Chromatic Sphere,"",1,fd71f597-ad12-4d2b-93af-3f8dfe4027b2,"Artifact","{1}, {T}, Sacrifice this artifact: Add one mana of any color. Draw a card."
            1,Evolving Wilds,"",0,31181bd2-3a1f-4cb9-ba30-637ac479133a,"Land","{T}, Sacrifice this land: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle."
            1,Access Tunnel,"",0,4bef5957-71a4-4fe0-b2ce-dff8e8690bd9,"Land","{T}: Add {C}. {3}, {T}: Target creature with power 3 or less can't be blocked this turn."
            1,Goblin,"Red",0,e265ca24-96c0-4654-a8f3-bbffe288970a,"Creature,Token","undefined // undefined"
            1,On an Adventure,"",0,fcf4c7fb-7859-4c11-8552-6817f5119d2e,"Card","After an Adventure resolves, you can place the exiled card here. You may cast the creature from exile."
            1,Mask of Memory,"",2,c6c4dffd-0ae9-493d-afa4-d1eb8bdba582,"Artifact","Whenever equipped creature deals combat damage to a player, you may draw two cards. If you do, discard a card. Equip {1}"
        """)
    )
    return csv_path


@pytest.fixture
def real_cube_path() -> Path:
    """Path to the real cube CSV file."""
    return Path(__file__).parent.parent / "regular-cube.csv"


@pytest.fixture
def sample_scryfall_path(tmp_path: Path) -> Path:
    """Create a small Scryfall bulk JSON file for testing."""
    data = [
        {
            "id": "e3285e6b-3e79-4d7c-bf96-d920f973b122",
            "oracle_id": "orc-bolt",
            "name": "Lightning Bolt",
            "keywords": ["Prowess"],
        },
        {
            "id": "1920dae4-fb92-4f19-ae4b-eb3276b8571c",
            "oracle_id": "orc-counter",
            "name": "Counterspell",
            "keywords": [],
        },
        {
            "id": "71d9fd43-576f-45db-ab8f-a9f2a0427398",
            "oracle_id": "orc-anax",
            "name": "Anax and Cymede",
            "keywords": ["Heroic"],
        },
        {
            "id": "fd71f597-ad12-4d2b-93af-3f8dfe4027b2",
            "oracle_id": "orc-sphere",
            "name": "Chromatic Sphere",
            "keywords": [],
            "produced_mana": ["W", "U", "B", "R", "G"],
        },
        {
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "oracle_id": "orc-other",
            "name": "Some Other Card",
            "keywords": ["Flying", "Trample"],
        },
    ]
    scryfall_path = tmp_path / "scryfall.json"
    scryfall_path.write_text(json.dumps(data))
    return scryfall_path


@pytest.fixture
def sample_tags_cache(tmp_path: Path) -> Path:
    """Create a sample Scryfall oracle tags cache file for testing."""
    cache = {
        "fetched_at": "2026-02-14T00:00:00+00:00",
        "tags": {
            "burn": ["orc-bolt"],
            "removal": ["orc-bolt", "orc-counter"],
            "counterspell": ["orc-counter"],
            "ramp": ["orc-sphere"],
        },
    }
    cache_path = tmp_path / "tags-cache.json"
    cache_path.write_text(json.dumps(cache))
    return cache_path


def _make_card(name, colors, types, text=""):
    """Helper to create a Card with all required fields."""
    return Card(
        name=name,
        colors=colors,
        cmc=2,
        scryfall_id=f"id-{name.lower().replace(' ', '-')}",
        types=types,
        text=text,
        keywords=[],
        oracle_id="",
        produced_mana=[],
        functional_tags=[],
    )


@pytest.fixture
def sample_cards() -> list[Card]:
    """Create a sample set of cards for pack generation testing.

    10 cards per mono color, 10 multicolor, 10 lands, 5 fixing artifacts,
    5 colorless artifacts = 80 cards total.
    """
    cards: list[Card] = []

    # 10 white creatures
    for i in range(1, 11):
        cards.append(_make_card(f"White Knight {i}", ["White"], ["Creature"]))

    # 10 blue creatures
    for i in range(1, 11):
        cards.append(_make_card(f"Blue Wizard {i}", ["Blue"], ["Creature"]))

    # 10 black creatures
    for i in range(1, 11):
        cards.append(_make_card(f"Black Shade {i}", ["Black"], ["Creature"]))

    # 10 red creatures
    for i in range(1, 11):
        cards.append(_make_card(f"Red Goblin {i}", ["Red"], ["Creature"]))

    # 10 green creatures
    for i in range(1, 11):
        cards.append(_make_card(f"Green Elf {i}", ["Green"], ["Creature"]))

    # 10 multicolor creatures
    for i in range(1, 11):
        cards.append(_make_card(f"Gold Card {i}", ["White", "Blue"], ["Creature"]))

    # 10 lands
    for i in range(1, 11):
        cards.append(_make_card(f"Dual Land {i}", [], ["Land"]))

    # 5 fixing artifacts
    for i in range(1, 6):
        cards.append(
            _make_card(
                f"Mana Rock {i}",
                [],
                ["Artifact"],
                text="Add one mana of any color.",
            )
        )

    # 5 colorless artifacts (non-fixing)
    for i in range(1, 6):
        cards.append(
            _make_card(
                f"Equipment {i}",
                [],
                ["Artifact"],
                text="Equipped creature gets +1/+1.",
            )
        )

    return cards
