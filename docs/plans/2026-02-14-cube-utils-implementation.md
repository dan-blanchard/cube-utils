# cube_utils Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python CLI tool that generates seeded draft packs and a draft guide skeleton for an MTG cube.

**Architecture:** Single Python package (`cube_utils`) with a Click CLI exposing two commands: `packs` and `guide`. Card data is loaded from a CSV file and optionally enriched with Scryfall bulk JSON. Pack generation uses a seeded structure ensuring color balance. Guide generation detects themes by scanning card text for keyword patterns.

**Tech Stack:** Python 3.11+, Click (CLI), pytest (testing), csv/json stdlib modules.

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/cube_utils/__init__.py`
- Create: `src/cube_utils/cli.py`

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "cube-utils"
version = "0.1.0"
description = "MTG cube draft utilities"
requires-python = ">=3.11"
dependencies = ["click>=8.0"]

[project.scripts]
cube-utils = "cube_utils.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Step 2: Create package init**

```python
# src/cube_utils/__init__.py
```

(Empty file.)

**Step 3: Create CLI skeleton**

```python
# src/cube_utils/cli.py
import click


@click.group()
def main():
    """MTG cube draft utilities."""


@main.command()
def packs():
    """Generate draft packs."""
    click.echo("packs command (not yet implemented)")


@main.command()
def guide():
    """Generate draft guide skeleton."""
    click.echo("guide command (not yet implemented)")
```

**Step 4: Install in dev mode and verify CLI works**

Run: `pip install -e '.[dev]' && cube-utils --help`
Expected: Help text showing `packs` and `guide` commands.

**Step 5: Commit**

```bash
git add pyproject.toml src/
git commit --no-gpg-sign -m "feat: project scaffolding with Click CLI skeleton"
```

---

### Task 2: Card Data Model and CSV Loading

**Files:**
- Create: `src/cube_utils/cards.py`
- Create: `tests/test_cards.py`
- Create: `tests/conftest.py`

**Step 1: Write failing tests for Card model and CSV loading**

```python
# tests/conftest.py
import csv
import io
import pytest


SAMPLE_CSV = """\
quantity,card name,color,cmc,scryfall ID,types,card text
1,Adanto Vanguard,White,2,21c950d7-b4f6-4902-8c9a-98f2933f9fa5,Creature,"As long as this creature is attacking, it gets +2/+0. Pay 4 life: This creature gains indestructible until end of turn."
1,Counterspell,Blue,2,3320f04a-9a24-4b81-a741-b7b5e3760e5c,Instant,Counter target spell.
1,Chromatic Sphere,,1,fd71f597-ad12-4d2b-93af-3f8dfe4027b2,Artifact,"{1}, {T}, Sacrifice this artifact: Add one mana of any color. Draw a card."
1,Stomping Ground,,0,00000000-0000-0000-0000-000000000001,Land,
1,Soldier,,0,00000000-0000-0000-0000-000000000002,"Creature,Token",
1,"Anax and Cymede","White,Red",3,71d9fd43-576f-45db-ab8f-a9f2a0427398,Creature,"First strike, vigilance Heroic — Whenever you cast a spell that targets Anax and Cymede, creatures you control get +1/+1 and gain trample until end of turn."
"""


@pytest.fixture
def sample_csv_path(tmp_path):
    p = tmp_path / "test_cube.csv"
    p.write_text(SAMPLE_CSV)
    return p
```

```python
# tests/test_cards.py
from cube_utils.cards import Card, load_cube


def test_load_cube_returns_list_of_cards(sample_csv_path):
    cards = load_cube(sample_csv_path)
    assert isinstance(cards, list)
    assert all(isinstance(c, Card) for c in cards)


def test_load_cube_excludes_tokens(sample_csv_path):
    cards = load_cube(sample_csv_path)
    names = [c.name for c in cards]
    assert "Soldier" not in names


def test_load_cube_parses_fields(sample_csv_path):
    cards = load_cube(sample_csv_path)
    vanguard = next(c for c in cards if c.name == "Adanto Vanguard")
    assert vanguard.colors == ["White"]
    assert vanguard.cmc == 2
    assert vanguard.types == ["Creature"]
    assert "indestructible" in vanguard.text


def test_load_cube_parses_multicolor(sample_csv_path):
    cards = load_cube(sample_csv_path)
    anax = next(c for c in cards if c.name == "Anax and Cymede")
    assert anax.colors == ["White", "Red"]


def test_load_cube_parses_colorless(sample_csv_path):
    cards = load_cube(sample_csv_path)
    sphere = next(c for c in cards if c.name == "Chromatic Sphere")
    assert sphere.colors == []
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cards.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cube_utils.cards'`

**Step 3: Implement Card model and load_cube**

```python
# src/cube_utils/cards.py
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Card:
    name: str
    colors: list[str]
    cmc: int
    scryfall_id: str
    types: list[str]
    text: str

    @property
    def is_multicolor(self) -> bool:
        return len(self.colors) > 1

    @property
    def is_colorless(self) -> bool:
        return len(self.colors) == 0

    @property
    def is_land(self) -> bool:
        return self.is_colorless and "Land" in self.types

    @property
    def is_token(self) -> bool:
        return "Token" in self.types

    @property
    def is_draftable(self) -> bool:
        return not self.is_token and "Card" not in self.types


NON_DRAFTABLE_TYPES = {"Token", "Card"}


def load_cube(path: Path) -> list[Card]:
    """Load cube card list from CSV, excluding non-draftable entries."""
    cards = []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            types = [t.strip() for t in row[5].split(",")]
            if any(t in NON_DRAFTABLE_TYPES for t in types):
                continue
            colors = [c.strip() for c in row[2].split(",") if c.strip()]
            cmc = int(row[3]) if row[3] else 0
            text = ",".join(row[6:])  # rejoin text that was split on commas
            cards.append(Card(
                name=row[1],
                colors=colors,
                cmc=cmc,
                scryfall_id=row[4],
                types=types,
                text=text,
            ))
    return cards
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cards.py -v`
Expected: All 5 tests PASS.

**Step 5: Commit**

```bash
git add src/cube_utils/cards.py tests/conftest.py tests/test_cards.py
git commit --no-gpg-sign -m "feat: Card data model and CSV loading with token exclusion"
```

---

### Task 3: Card Categorization

**Files:**
- Modify: `src/cube_utils/cards.py`
- Modify: `tests/test_cards.py`

**Step 1: Write failing tests for categorization**

Add to `tests/test_cards.py`:

```python
from cube_utils.cards import Card, load_cube, categorize_cards, Category


def test_categorize_mono_color(sample_csv_path):
    cards = load_cube(sample_csv_path)
    cats = categorize_cards(cards)
    assert any(c.name == "Adanto Vanguard" for c in cats[Category.MONO_WHITE])
    assert any(c.name == "Counterspell" for c in cats[Category.MONO_BLUE])


def test_categorize_multicolor(sample_csv_path):
    cards = load_cube(sample_csv_path)
    cats = categorize_cards(cards)
    assert any(c.name == "Anax and Cymede" for c in cats[Category.MULTICOLOR])


def test_categorize_land(sample_csv_path):
    cards = load_cube(sample_csv_path)
    cats = categorize_cards(cards)
    assert any(c.name == "Stomping Ground" for c in cats[Category.LAND])


def test_categorize_fixing(sample_csv_path):
    cards = load_cube(sample_csv_path)
    cats = categorize_cards(cards)
    assert any(c.name == "Chromatic Sphere" for c in cats[Category.FIXING])


def test_every_card_categorized_exactly_once(sample_csv_path):
    cards = load_cube(sample_csv_path)
    cats = categorize_cards(cards)
    all_categorized = []
    for card_list in cats.values():
        all_categorized.extend(card_list)
    assert len(all_categorized) == len(cards)
    assert set(c.name for c in all_categorized) == set(c.name for c in cards)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cards.py -v -k categorize`
Expected: FAIL — `ImportError: cannot import name 'categorize_cards'`

**Step 3: Implement categorization**

Add to `src/cube_utils/cards.py`:

```python
from enum import Enum


class Category(Enum):
    MONO_WHITE = "mono_white"
    MONO_BLUE = "mono_blue"
    MONO_BLACK = "mono_black"
    MONO_RED = "mono_red"
    MONO_GREEN = "mono_green"
    MULTICOLOR = "multicolor"
    LAND = "land"
    FIXING = "fixing"
    COLORLESS = "colorless"


MONO_COLOR_CATEGORIES = {
    "White": Category.MONO_WHITE,
    "Blue": Category.MONO_BLUE,
    "Black": Category.MONO_BLACK,
    "Red": Category.MONO_RED,
    "Green": Category.MONO_GREEN,
}

FIXING_PATTERNS = [
    "mana of any color",
    "search your library for a basic land",
    "add one mana",
]


def _is_fixing(card: Card) -> bool:
    """Detect colorless mana-fixing cards by text patterns."""
    text_lower = card.text.lower()
    return any(pattern in text_lower for pattern in FIXING_PATTERNS)


def categorize_cards(cards: list[Card]) -> dict[Category, list[Card]]:
    """Assign each card to exactly one category."""
    result: dict[Category, list[Card]] = {cat: [] for cat in Category}
    for card in cards:
        if card.is_multicolor:
            result[Category.MULTICOLOR].append(card)
        elif card.is_land:
            result[Category.LAND].append(card)
        elif card.is_colorless and _is_fixing(card):
            result[Category.FIXING].append(card)
        elif card.is_colorless:
            result[Category.COLORLESS].append(card)
        elif len(card.colors) == 1:
            cat = MONO_COLOR_CATEGORIES[card.colors[0]]
            result[cat].append(card)
    return result
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cards.py -v`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add src/cube_utils/cards.py tests/test_cards.py
git commit --no-gpg-sign -m "feat: card categorization into draft pool categories"
```

---

### Task 4: Scryfall Enrichment

**Files:**
- Modify: `src/cube_utils/cards.py`
- Modify: `tests/test_cards.py`
- Modify: `tests/conftest.py`

The Scryfall bulk JSON contains full card data keyed by `id`. We load only the cards matching scryfall IDs from the cube to add keywords and other metadata useful for guide generation.

**Step 1: Write failing tests**

Add to `tests/conftest.py`:

```python
import json

SAMPLE_SCRYFALL = [
    {
        "id": "21c950d7-b4f6-4902-8c9a-98f2933f9fa5",
        "name": "Adanto Vanguard",
        "keywords": ["Indestructible"],
        "color_identity": ["W"],
    },
    {
        "id": "3320f04a-9a24-4b81-a741-b7b5e3760e5c",
        "name": "Counterspell",
        "keywords": [],
        "color_identity": ["U"],
    },
    {
        "id": "fd71f597-ad12-4d2b-93af-3f8dfe4027b2",
        "name": "Chromatic Sphere",
        "keywords": [],
        "color_identity": [],
    },
]


@pytest.fixture
def sample_scryfall_path(tmp_path):
    p = tmp_path / "scryfall.json"
    p.write_text(json.dumps(SAMPLE_SCRYFALL))
    return p
```

Add to `tests/test_cards.py`:

```python
from cube_utils.cards import enrich_with_scryfall


def test_enrich_adds_keywords(sample_csv_path, sample_scryfall_path):
    cards = load_cube(sample_csv_path)
    enrich_with_scryfall(cards, sample_scryfall_path)
    vanguard = next(c for c in cards if c.name == "Adanto Vanguard")
    assert "Indestructible" in vanguard.keywords


def test_enrich_skips_missing_ids(sample_csv_path, sample_scryfall_path):
    cards = load_cube(sample_csv_path)
    enrich_with_scryfall(cards, sample_scryfall_path)
    # Cards not in scryfall data should have empty keywords
    anax = next(c for c in cards if c.name == "Anax and Cymede")
    assert anax.keywords == []
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cards.py -v -k enrich`
Expected: FAIL — `ImportError: cannot import name 'enrich_with_scryfall'`

**Step 3: Implement enrichment**

Add `keywords` field to `Card` dataclass:

```python
@dataclass
class Card:
    name: str
    colors: list[str]
    cmc: int
    scryfall_id: str
    types: list[str]
    text: str
    keywords: list[str] = field(default_factory=list)
```

Add function:

```python
import json


def enrich_with_scryfall(cards: list[Card], scryfall_path: Path) -> None:
    """Enrich cards with keyword data from Scryfall bulk JSON."""
    cube_ids = {c.scryfall_id for c in cards}
    lookup: dict[str, dict] = {}
    with open(scryfall_path) as f:
        for entry in json.load(f):
            if entry["id"] in cube_ids:
                lookup[entry["id"]] = entry
    for card in cards:
        data = lookup.get(card.scryfall_id, {})
        card.keywords = data.get("keywords", [])
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cards.py -v`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add src/cube_utils/cards.py tests/conftest.py tests/test_cards.py
git commit --no-gpg-sign -m "feat: Scryfall enrichment for keyword metadata"
```

---

### Task 5: Theme Detection

**Files:**
- Create: `src/cube_utils/guide.py`
- Create: `tests/test_guide.py`

Theme detection scans card text for keyword clusters and assigns cards to themes. A card can belong to multiple themes.

**Step 1: Write failing tests**

```python
# tests/test_guide.py
from cube_utils.cards import Card
from cube_utils.guide import detect_themes, Theme


def _make_card(name, colors=None, text="", types=None, keywords=None):
    return Card(
        name=name,
        colors=colors or [],
        cmc=2,
        scryfall_id="test",
        types=types or ["Creature"],
        text=text,
        keywords=keywords or [],
    )


def test_detect_sacrifice_theme():
    cards = [
        _make_card("Sac Outlet", text="Sacrifice a creature: draw a card"),
        _make_card("Vanilla Bear", text=""),
    ]
    themes = detect_themes(cards)
    sac = themes[Theme.SACRIFICE]
    assert any(c.name == "Sac Outlet" for c in sac)
    assert not any(c.name == "Vanilla Bear" for c in sac)


def test_detect_counters_theme():
    cards = [
        _make_card("Counter Guy", text="put a +1/+1 counter on it"),
    ]
    themes = detect_themes(cards)
    assert any(c.name == "Counter Guy" for c in themes[Theme.COUNTERS])


def test_detect_etb_theme():
    cards = [
        _make_card("ETB Creature", text="When this creature enters, draw a card"),
    ]
    themes = detect_themes(cards)
    assert any(c.name == "ETB Creature" for c in themes[Theme.ETB])


def test_detect_spells_matter_theme():
    cards = [
        _make_card("Prowess Guy", text="Prowess", keywords=["Prowess"]),
        _make_card("Spell Payoff", text="Whenever you cast a noncreature spell"),
    ]
    themes = detect_themes(cards)
    assert len(themes[Theme.SPELLS_MATTER]) == 2


def test_card_can_belong_to_multiple_themes():
    cards = [
        _make_card("Bridge Card", text="Sacrifice a creature: put a +1/+1 counter on target creature"),
    ]
    themes = detect_themes(cards)
    assert any(c.name == "Bridge Card" for c in themes[Theme.SACRIFICE])
    assert any(c.name == "Bridge Card" for c in themes[Theme.COUNTERS])
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_guide.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cube_utils.guide'`

**Step 3: Implement theme detection**

```python
# src/cube_utils/guide.py
from __future__ import annotations

from enum import Enum

from cube_utils.cards import Card


class Theme(Enum):
    SACRIFICE = "sacrifice"
    COUNTERS = "+1/+1 counters"
    ETB = "enters the battlefield"
    SPELLS_MATTER = "spells matter"
    TOKENS = "tokens"
    ARTIFACTS = "artifacts matter"
    BLINK = "blink/flicker"
    HEROIC = "heroic/targeting"
    CYCLING = "cycling/discard"
    EQUIPMENT = "equipment"
    GRAVEYARD = "graveyard"
    AGGRO = "aggro/haste"
    EVASION = "evasion"
    RAMP = "ramp/lands"


# Each theme has a list of text patterns (matched case-insensitively against card text)
# and optional keyword matches (matched against the keywords list from Scryfall).
THEME_PATTERNS: dict[Theme, dict] = {
    Theme.SACRIFICE: {
        "text": ["sacrifice a", "sacrifice this", "when this creature dies",
                 "whenever a creature dies", "whenever a creature you control dies"],
    },
    Theme.COUNTERS: {
        "text": ["+1/+1 counter", "modular", "-1/-1 counter"],
    },
    Theme.ETB: {
        "text": ["when this creature enters", "when this artifact enters",
                 "when this enchantment enters", "when it enters",
                 "enters the battlefield", "enters, "],
    },
    Theme.SPELLS_MATTER: {
        "text": ["noncreature spell", "instant or sorcery", "prowess",
                 "magecraft"],
        "keywords": ["Prowess"],
    },
    Theme.TOKENS: {
        "text": ["create a", "create two", "creature token", "artifact token"],
    },
    Theme.ARTIFACTS: {
        "text": ["artifact you control", "target artifact",
                 "historic", "whenever you cast an artifact"],
    },
    Theme.BLINK: {
        "text": ["exile target creature you control, then return",
                 "exile it, then return", "flicker"],
    },
    Theme.HEROIC: {
        "text": ["heroic", "whenever you cast a spell that targets",
                 "target creature you control gets",
                 "target creature gets +"],
        "keywords": ["Heroic"],
    },
    Theme.CYCLING: {
        "text": ["cycling", "discard a card", "discard this card",
                 "whenever you cycle", "whenever you discard"],
        "keywords": ["Cycling"],
    },
    Theme.EQUIPMENT: {
        "text": ["equip ", "equipped creature", "attach"],
        "keywords": ["Equip"],
    },
    Theme.GRAVEYARD: {
        "text": ["return target creature card from your graveyard",
                 "return target card from your graveyard",
                 "from your graveyard to your hand",
                 "from your graveyard to the battlefield",
                 "escape", "embalm", "unearth", "flashback"],
        "keywords": ["Escape", "Embalm", "Unearth", "Flashback"],
    },
    Theme.AGGRO: {
        "text": ["haste", "can't block", "attacks each combat if able"],
        "keywords": ["Haste"],
    },
    Theme.EVASION: {
        "text": ["can't be blocked", "menace", "shadow"],
        "keywords": ["Flying", "Menace", "Shadow"],
    },
    Theme.RAMP: {
        "text": ["search your library for a basic land",
                 "add one mana", "mana of any color",
                 "put that card onto the battlefield"],
    },
}


def detect_themes(cards: list[Card]) -> dict[Theme, list[Card]]:
    """Detect which themes each card participates in."""
    result: dict[Theme, list[Card]] = {theme: [] for theme in Theme}
    for card in cards:
        text_lower = card.text.lower()
        for theme, patterns in THEME_PATTERNS.items():
            matched = False
            for pattern in patterns.get("text", []):
                if pattern.lower() in text_lower:
                    matched = True
                    break
            if not matched:
                for kw in patterns.get("keywords", []):
                    if kw in card.keywords:
                        matched = True
                        break
            if matched:
                result[theme].append(card)
    return result
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_guide.py -v`
Expected: All 5 tests PASS.

**Step 5: Commit**

```bash
git add src/cube_utils/guide.py tests/test_guide.py
git commit --no-gpg-sign -m "feat: theme detection via keyword/text pattern matching"
```

---

### Task 6: Color Pair Analysis and Bridge Card Detection

**Files:**
- Modify: `src/cube_utils/guide.py`
- Modify: `tests/test_guide.py`

**Step 1: Write failing tests**

Add to `tests/test_guide.py`:

```python
from cube_utils.guide import (
    detect_themes, Theme, analyze_color_pairs, find_bridge_cards,
    ColorPairAnalysis,
)
from cube_utils.cards import categorize_cards


def test_analyze_color_pairs_finds_multicolor_cards():
    cards = [
        _make_card("WU Gold", colors=["White", "Blue"], text="flying"),
        _make_card("WR Gold", colors=["White", "Red"], text="haste"),
        _make_card("Mono W", colors=["White"], text="vigilance"),
    ]
    pairs = analyze_color_pairs(cards, detect_themes(cards))
    wu = next(p for p in pairs if p.colors == ("Blue", "White"))
    assert any(c.name == "WU Gold" for c in wu.multicolor_cards)
    assert not any(c.name == "WR Gold" for c in wu.multicolor_cards)


def test_analyze_color_pairs_finds_shared_themes():
    cards = [
        _make_card("W Sac", colors=["White"], text="Sacrifice a creature"),
        _make_card("B Sac", colors=["Black"], text="Whenever a creature dies"),
        _make_card("R Haste", colors=["Red"], text="Haste", keywords=["Haste"]),
    ]
    pairs = analyze_color_pairs(cards, detect_themes(cards))
    wb = next(p for p in pairs if p.colors == ("Black", "White"))
    assert Theme.SACRIFICE in wb.shared_themes


def test_find_bridge_cards():
    cards = [
        _make_card("Bridge", text="Sacrifice a creature: put a +1/+1 counter"),
        _make_card("Single Theme", text="Sacrifice a creature"),
        _make_card("No Theme", text="vanilla"),
    ]
    themes = detect_themes(cards)
    bridges = find_bridge_cards(themes)
    assert any(c.name == "Bridge" for c in bridges)
    assert not any(c.name == "Single Theme" for c in bridges)
    assert not any(c.name == "No Theme" for c in bridges)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_guide.py -v -k "color_pair or bridge"`
Expected: FAIL — `ImportError: cannot import name 'analyze_color_pairs'`

**Step 3: Implement color pair analysis and bridge detection**

Add to `src/cube_utils/guide.py`:

```python
from dataclasses import dataclass
from itertools import combinations

COLOR_ORDER = ["White", "Blue", "Black", "Red", "Green"]
COLOR_PAIRS = list(combinations(sorted(COLOR_ORDER), 2))


@dataclass
class ColorPairAnalysis:
    colors: tuple[str, str]
    multicolor_cards: list[Card]
    shared_themes: list[Theme]
    theme_cards: dict[Theme, list[Card]]  # cards in this color pair supporting each shared theme


def _card_in_colors(card: Card, pair: tuple[str, str]) -> bool:
    """Check if a mono card's color is in the pair, or a multi card's colors are a subset."""
    if card.is_colorless:
        return False
    if card.is_multicolor:
        return set(card.colors).issubset(set(pair))
    return card.colors[0] in pair


def analyze_color_pairs(
    cards: list[Card], themes: dict[Theme, list[Card]]
) -> list[ColorPairAnalysis]:
    """Analyze each two-color pair for multicolor cards and shared themes."""
    results = []
    for pair in COLOR_PAIRS:
        multi = [c for c in cards if c.is_multicolor and set(c.colors) == set(pair)]
        # Find themes where both colors contribute
        shared = []
        theme_cards_map: dict[Theme, list[Card]] = {}
        for theme, theme_card_list in themes.items():
            colors_present = set()
            pair_cards = []
            for c in theme_card_list:
                if _card_in_colors(c, pair):
                    colors_present.update(c.colors if c.colors else [])
                    pair_cards.append(c)
            if pair[0] in colors_present and pair[1] in colors_present:
                shared.append(theme)
                theme_cards_map[theme] = pair_cards
        results.append(ColorPairAnalysis(
            colors=pair,
            multicolor_cards=multi,
            shared_themes=shared,
            theme_cards=theme_cards_map,
        ))
    return results


def find_bridge_cards(themes: dict[Theme, list[Card]]) -> list[Card]:
    """Find cards that appear in 2+ themes."""
    card_theme_count: dict[str, int] = {}
    card_lookup: dict[str, Card] = {}
    for theme_cards in themes.values():
        for card in theme_cards:
            card_theme_count[card.name] = card_theme_count.get(card.name, 0) + 1
            card_lookup[card.name] = card
    return [card_lookup[name] for name, count in card_theme_count.items() if count >= 2]
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_guide.py -v`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add src/cube_utils/guide.py tests/test_guide.py
git commit --no-gpg-sign -m "feat: color pair analysis and bridge card detection"
```

---

### Task 7: Guide Markdown Output and CLI Command

**Files:**
- Modify: `src/cube_utils/guide.py`
- Modify: `src/cube_utils/cli.py`
- Modify: `tests/test_guide.py`

**Step 1: Write failing tests**

Add to `tests/test_guide.py`:

```python
from cube_utils.guide import generate_guide_markdown


def test_generate_guide_markdown_has_sections():
    cards = [
        _make_card("W Sac", colors=["White"], text="Sacrifice a creature: draw a card"),
        _make_card("B Sac", colors=["Black"], text="Whenever a creature you control dies, draw"),
        _make_card("WB Gold", colors=["White", "Black"], text="Sacrifice: drain 1"),
        _make_card("Counter Guy", colors=["Green"], text="+1/+1 counter"),
    ]
    themes = detect_themes(cards)
    pairs = analyze_color_pairs(cards, themes)
    bridges = find_bridge_cards(themes)
    md = generate_guide_markdown(themes, pairs, bridges)
    assert "# Draft Guide Skeleton" in md
    assert "## Themes" in md
    assert "## Color Pairs" in md
    assert "## Bridge Cards" in md
    assert "sacrifice" in md.lower()


def test_generate_guide_markdown_lists_cards():
    cards = [
        _make_card("Sac Outlet", colors=["Black"], text="Sacrifice a creature"),
    ]
    themes = detect_themes(cards)
    pairs = analyze_color_pairs(cards, themes)
    bridges = find_bridge_cards(themes)
    md = generate_guide_markdown(themes, pairs, bridges)
    assert "Sac Outlet" in md
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_guide.py -v -k markdown`
Expected: FAIL — `ImportError: cannot import name 'generate_guide_markdown'`

**Step 3: Implement markdown generation**

Add to `src/cube_utils/guide.py`:

```python
COLOR_PAIR_NAMES = {
    ("Black", "Blue"): "Dimir",
    ("Black", "Green"): "Golgari",
    ("Black", "Red"): "Rakdos",
    ("Black", "White"): "Orzhov",
    ("Blue", "Green"): "Simic",
    ("Blue", "Red"): "Izzet",
    ("Blue", "White"): "Azorius",
    ("Green", "Red"): "Gruul",
    ("Green", "White"): "Selesnya",
    ("Red", "White"): "Boros",
}

COLOR_ABBREV = {
    "White": "W", "Blue": "U", "Black": "B", "Red": "R", "Green": "G",
}


def generate_guide_markdown(
    themes: dict[Theme, list[Card]],
    pairs: list[ColorPairAnalysis],
    bridges: list[Card],
) -> str:
    """Generate a draft guide skeleton as markdown."""
    lines = ["# Draft Guide Skeleton", ""]

    # Themes section
    lines.append("## Themes")
    lines.append("")
    for theme in Theme:
        cards = themes[theme]
        if not cards:
            continue
        lines.append(f"### {theme.value.title()} ({len(cards)} cards)")
        lines.append("")
        # Group by color
        by_color: dict[str, list[str]] = {}
        for card in cards:
            if card.is_multicolor:
                key = "".join(COLOR_ABBREV.get(c, "?") for c in sorted(card.colors))
            elif card.colors:
                key = COLOR_ABBREV.get(card.colors[0], "?")
            else:
                key = "C"
            by_color.setdefault(key, []).append(card.name)
        for color_key in sorted(by_color):
            names = ", ".join(sorted(by_color[color_key]))
            lines.append(f"- **{color_key}**: {names}")
        lines.append("")

    # Color pairs section
    lines.append("## Color Pairs")
    lines.append("")
    for pair in pairs:
        guild = COLOR_PAIR_NAMES.get(pair.colors, "?")
        abbrev = "".join(COLOR_ABBREV.get(c, "?") for c in pair.colors)
        lines.append(f"### {guild} ({abbrev})")
        lines.append("")
        if pair.multicolor_cards:
            names = ", ".join(c.name for c in pair.multicolor_cards)
            lines.append(f"**Gold cards:** {names}")
            lines.append("")
        if pair.shared_themes:
            theme_names = ", ".join(t.value for t in pair.shared_themes)
            lines.append(f"**Shared themes:** {theme_names}")
            lines.append("")
            for theme in pair.shared_themes:
                theme_cards = pair.theme_cards.get(theme, [])
                if theme_cards:
                    names = ", ".join(c.name for c in theme_cards)
                    lines.append(f"- *{theme.value}*: {names}")
            lines.append("")
        if not pair.multicolor_cards and not pair.shared_themes:
            lines.append("*(No strong theme overlap detected)*")
            lines.append("")

    # Bridge cards section
    lines.append("## Bridge Cards")
    lines.append("")
    lines.append("Cards that participate in 2+ themes:")
    lines.append("")
    if bridges:
        # List each bridge card with its themes
        card_themes: dict[str, list[str]] = {}
        for theme, theme_cards in themes.items():
            for card in theme_cards:
                if any(b.name == card.name for b in bridges):
                    card_themes.setdefault(card.name, []).append(theme.value)
        for name in sorted(card_themes):
            theme_list = ", ".join(card_themes[name])
            lines.append(f"- **{name}**: {theme_list}")
    lines.append("")

    return "\n".join(lines)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_guide.py -v`
Expected: All tests PASS.

**Step 5: Wire up the CLI command**

Update `src/cube_utils/cli.py`:

```python
# src/cube_utils/cli.py
from pathlib import Path

import click

from cube_utils.cards import load_cube, categorize_cards, enrich_with_scryfall
from cube_utils.guide import (
    detect_themes, analyze_color_pairs, find_bridge_cards,
    generate_guide_markdown,
)


@click.group()
def main():
    """MTG cube draft utilities."""


@main.command()
@click.option("--cube", "cube_path", default="cube-2.csv",
              type=click.Path(exists=True), help="Path to cube CSV file.")
@click.option("--scryfall", "scryfall_path", default=None,
              type=click.Path(exists=True), help="Path to Scryfall bulk JSON.")
@click.option("--output", "output_path", default=None,
              type=click.Path(), help="Write output to file instead of stdout.")
def guide(cube_path, scryfall_path, output_path):
    """Generate draft guide skeleton."""
    cards = load_cube(Path(cube_path))
    if scryfall_path:
        enrich_with_scryfall(cards, Path(scryfall_path))
    themes = detect_themes(cards)
    pairs = analyze_color_pairs(cards, themes)
    bridges = find_bridge_cards(themes)
    md = generate_guide_markdown(themes, pairs, bridges)
    if output_path:
        Path(output_path).write_text(md)
        click.echo(f"Guide written to {output_path}")
    else:
        click.echo(md)


@main.command()
def packs():
    """Generate draft packs."""
    click.echo("packs command (not yet implemented)")
```

**Step 6: Test CLI manually**

Run: `cube-utils guide --cube cube-2.csv | head -50`
Expected: Markdown output starting with `# Draft Guide Skeleton` and theme sections.

**Step 7: Commit**

```bash
git add src/cube_utils/guide.py src/cube_utils/cli.py tests/test_guide.py
git commit --no-gpg-sign -m "feat: guide markdown generation and CLI command"
```

---

### Task 8: Review Guide Output and Iterate

This is a collaborative task. Run `cube-utils guide --cube cube-2.csv --scryfall default-cards-*.json` and review the output with the user. Adjust theme patterns, color pair analysis, or output formatting based on feedback.

No specific code steps — this is an interactive review session.

**Step 1: Run the guide generator**

Run: `cube-utils guide --cube cube-2.csv --scryfall default-cards-*.json --output docs/draft-guide-skeleton.md`

**Step 2: Review output with user and adjust theme patterns if needed**

**Step 3: Commit any adjustments**

```bash
git add src/cube_utils/guide.py docs/draft-guide-skeleton.md
git commit --no-gpg-sign -m "refine: tune theme patterns after reviewing guide output"
```

---

### Task 9: Write Draft Guide

Collaborative task — use the guide skeleton as a starting point and write `docs/draft-guide.md` with the user.

**Step 1: Create docs/draft-guide.md from skeleton, adding prose**

**Step 2: Commit**

```bash
git add docs/draft-guide.md
git commit --no-gpg-sign -m "docs: draft guide for cube"
```

---

### Task 10: Pack Structure Definitions

**Files:**
- Create: `src/cube_utils/packs.py`
- Create: `tests/test_packs.py`

**Step 1: Write failing tests for pack structure**

```python
# tests/test_packs.py
from cube_utils.packs import PackStructure, get_pack_structure


def test_default_15_card_structure():
    ps = get_pack_structure(15)
    assert ps.mono_per_color == 1
    assert ps.fixing == 1
    assert ps.colorless == 1
    # multi + land + extra_mono should sum to remaining (15 - 5 - 1 - 1 = 8)
    assert ps.total() == 15


def test_11_card_structure():
    ps = get_pack_structure(11)
    assert ps.mono_per_color == 1
    assert ps.fixing == 1
    assert ps.total() == 11


def test_9_card_structure():
    ps = get_pack_structure(9)
    assert ps.mono_per_color == 1
    assert ps.fixing == 1
    assert ps.total() == 9
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_packs.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cube_utils.packs'`

**Step 3: Implement pack structures**

```python
# src/cube_utils/packs.py
from __future__ import annotations

import random
from dataclasses import dataclass

from cube_utils.cards import Card, Category


@dataclass
class PackStructure:
    """Defines the slot distribution for a single pack."""
    mono_per_color: int  # guaranteed cards per mono color (always 1)
    colorless: int
    multicolor_range: tuple[int, int]  # (min, max) multicolor cards
    land_range: tuple[int, int]        # (min, max) land cards
    fixing: int
    extra_mono: int                     # additional random mono cards

    def total(self) -> int:
        mono = self.mono_per_color * 5
        # For total, use the average of ranges since they're complementary
        multi = self.multicolor_range[0]
        land = self.land_range[1]  # ranges sum to a constant
        return mono + self.colorless + multi + land + self.fixing + self.extra_mono


PACK_STRUCTURES = {
    15: PackStructure(
        mono_per_color=1,
        colorless=1,
        multicolor_range=(2, 3),
        land_range=(2, 3),
        fixing=1,
        extra_mono=2,
    ),
    11: PackStructure(
        mono_per_color=1,
        colorless=1,
        multicolor_range=(1, 2),
        land_range=(1, 2),
        fixing=1,
        extra_mono=0,
    ),
    9: PackStructure(
        mono_per_color=1,
        colorless=1,
        multicolor_range=(1, 1),
        land_range=(1, 1),
        fixing=1,
        extra_mono=0,
    ),
}


def get_pack_structure(pack_size: int) -> PackStructure:
    """Get the pack structure for a given pack size."""
    if pack_size in PACK_STRUCTURES:
        return PACK_STRUCTURES[pack_size]
    raise ValueError(
        f"No pack structure defined for size {pack_size}. "
        f"Supported sizes: {sorted(PACK_STRUCTURES.keys())}"
    )
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_packs.py -v`
Expected: All 3 tests PASS.

**Step 5: Commit**

```bash
git add src/cube_utils/packs.py tests/test_packs.py
git commit --no-gpg-sign -m "feat: pack structure definitions for 15/11/9-card packs"
```

---

### Task 11: Pack Template Generation

**Files:**
- Modify: `src/cube_utils/packs.py`
- Modify: `tests/test_packs.py`

**Step 1: Write failing tests**

Add to `tests/test_packs.py`:

```python
from cube_utils.packs import generate_pack_templates, PackTemplate


def test_generate_templates_correct_count():
    templates = generate_pack_templates(num_packs=3, pack_size=15)
    assert len(templates) == 3


def test_template_has_correct_total():
    templates = generate_pack_templates(num_packs=1, pack_size=15)
    t = templates[0]
    total = (t.white + t.blue + t.black + t.red + t.green +
             t.colorless + t.multicolor + t.land + t.fixing)
    assert total == 15


def test_template_guarantees_one_per_color():
    templates = generate_pack_templates(num_packs=10, pack_size=15)
    for t in templates:
        assert t.white >= 1
        assert t.blue >= 1
        assert t.black >= 1
        assert t.red >= 1
        assert t.green >= 1


def test_template_guarantees_one_fixing():
    templates = generate_pack_templates(num_packs=10, pack_size=15)
    for t in templates:
        assert t.fixing == 1


def test_template_9_card_packs():
    templates = generate_pack_templates(num_packs=1, pack_size=9)
    t = templates[0]
    total = (t.white + t.blue + t.black + t.red + t.green +
             t.colorless + t.multicolor + t.land + t.fixing)
    assert total == 9
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_packs.py -v -k template`
Expected: FAIL — `ImportError: cannot import name 'generate_pack_templates'`

**Step 3: Implement template generation**

Add to `src/cube_utils/packs.py`:

```python
COLORS = ["white", "blue", "black", "red", "green"]


@dataclass
class PackTemplate:
    """Counts per category for a single pack."""
    white: int = 0
    blue: int = 0
    black: int = 0
    red: int = 0
    green: int = 0
    colorless: int = 0
    multicolor: int = 0
    land: int = 0
    fixing: int = 0

    def total(self) -> int:
        return (self.white + self.blue + self.black + self.red + self.green +
                self.colorless + self.multicolor + self.land + self.fixing)


def generate_pack_templates(num_packs: int, pack_size: int) -> list[PackTemplate]:
    """Generate pack templates with randomized slot distribution."""
    structure = get_pack_structure(pack_size)
    templates = []
    for _ in range(num_packs):
        # Randomize multi/land split within their ranges
        multi_count = random.randint(*structure.multicolor_range)
        land_count = (structure.multicolor_range[0] + structure.land_range[1]) - multi_count

        # Start with 1 per color
        color_counts = {c: structure.mono_per_color for c in COLORS}

        # Distribute extra mono slots to random colors
        for _ in range(structure.extra_mono):
            color = random.choice(COLORS)
            color_counts[color] += 1

        templates.append(PackTemplate(
            white=color_counts["white"],
            blue=color_counts["blue"],
            black=color_counts["black"],
            red=color_counts["red"],
            green=color_counts["green"],
            colorless=structure.colorless,
            multicolor=multi_count,
            land=land_count,
            fixing=structure.fixing,
        ))
    return templates
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_packs.py -v`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add src/cube_utils/packs.py tests/test_packs.py
git commit --no-gpg-sign -m "feat: pack template generation with randomized slot distribution"
```

---

### Task 12: Pack Cards Generation

**Files:**
- Modify: `src/cube_utils/packs.py`
- Modify: `tests/test_packs.py`
- Modify: `tests/conftest.py`

**Step 1: Write failing tests**

Add to `tests/conftest.py`:

```python
from cube_utils.cards import Card


@pytest.fixture
def sample_cards():
    """Minimal set of cards covering all categories for pack testing."""
    cards = []
    for color in ["White", "Blue", "Black", "Red", "Green"]:
        for i in range(5):
            cards.append(Card(
                name=f"{color} Card {i}",
                colors=[color],
                cmc=2,
                scryfall_id=f"mono-{color.lower()}-{i}",
                types=["Creature"],
                text="vanilla",
            ))
    for i in range(5):
        cards.append(Card(
            name=f"Gold Card {i}",
            colors=["White", "Blue"],
            cmc=3,
            scryfall_id=f"multi-{i}",
            types=["Creature"],
            text="multicolor",
        ))
    for i in range(5):
        cards.append(Card(
            name=f"Land {i}",
            colors=[],
            cmc=0,
            scryfall_id=f"land-{i}",
            types=["Land"],
            text="",
        ))
    for i in range(3):
        cards.append(Card(
            name=f"Fixer {i}",
            colors=[],
            cmc=1,
            scryfall_id=f"fix-{i}",
            types=["Artifact"],
            text="Add one mana of any color",
        ))
    for i in range(3):
        cards.append(Card(
            name=f"Artifact {i}",
            colors=[],
            cmc=2,
            scryfall_id=f"art-{i}",
            types=["Artifact"],
            text="vanilla artifact",
        ))
    return cards
```

Add to `tests/test_packs.py`:

```python
from cube_utils.packs import generate_card_packs
from cube_utils.cards import categorize_cards


def test_card_packs_correct_count(sample_cards):
    cats = categorize_cards(sample_cards)
    packs = generate_card_packs(cats, num_packs=2, pack_size=9)
    assert len(packs) == 2


def test_card_packs_correct_size(sample_cards):
    cats = categorize_cards(sample_cards)
    packs = generate_card_packs(cats, num_packs=2, pack_size=9)
    for pack in packs:
        assert len(pack) == 9


def test_card_packs_no_duplicates_across_packs(sample_cards):
    cats = categorize_cards(sample_cards)
    packs = generate_card_packs(cats, num_packs=2, pack_size=9)
    all_names = []
    for pack in packs:
        all_names.extend(c.name for c in pack)
    assert len(all_names) == len(set(all_names))
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_packs.py -v -k card_packs`
Expected: FAIL — `ImportError: cannot import name 'generate_card_packs'`

**Step 3: Implement card pack generation**

Add to `src/cube_utils/packs.py`:

```python
CATEGORY_FOR_COLOR = {
    "white": Category.MONO_WHITE,
    "blue": Category.MONO_BLUE,
    "black": Category.MONO_BLACK,
    "red": Category.MONO_RED,
    "green": Category.MONO_GREEN,
}


def generate_card_packs(
    categorized: dict[Category, list[Card]],
    num_packs: int,
    pack_size: int,
) -> list[list[Card]]:
    """Generate packs with actual card draws from categorized pools."""
    # Copy pools so we can draw without modifying originals
    pools = {cat: list(cards) for cat, cards in categorized.items()}
    for pool in pools.values():
        random.shuffle(pool)

    templates = generate_pack_templates(num_packs, pack_size)
    packs: list[list[Card]] = []

    for template in templates:
        pack: list[Card] = []

        def draw(category: Category, count: int):
            for _ in range(count):
                if pools[category]:
                    pack.append(pools[category].pop())

        for color in COLORS:
            draw(CATEGORY_FOR_COLOR[color], getattr(template, color))
        draw(Category.COLORLESS, template.colorless)
        draw(Category.MULTICOLOR, template.multicolor)
        draw(Category.LAND, template.land)
        draw(Category.FIXING, template.fixing)

        packs.append(pack)

    return packs
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_packs.py -v`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add src/cube_utils/packs.py tests/test_packs.py tests/conftest.py
git commit --no-gpg-sign -m "feat: card-level pack generation drawing from categorized pools"
```

---

### Task 13: Packs CLI Command

**Files:**
- Modify: `src/cube_utils/cli.py`

**Step 1: Implement the packs CLI command**

Update the `packs` command in `src/cube_utils/cli.py`:

```python
from cube_utils.packs import generate_pack_templates, generate_card_packs


@main.command()
@click.option("--cube", "cube_path", default="cube-2.csv",
              type=click.Path(exists=True), help="Path to cube CSV file.")
@click.option("--players", default=8, help="Number of players.")
@click.option("--packs", "num_packs_per_player", default=3, help="Packs per player.")
@click.option("--pack-size", default=15, help="Cards per pack.")
@click.option("--cards", "show_cards", is_flag=True, help="Show individual card names.")
@click.option("--output-dir", default=None, type=click.Path(),
              help="Write packs to files in this directory.")
def packs(cube_path, players, num_packs_per_player, pack_size, show_cards, output_dir):
    """Generate draft packs."""
    total_packs = players * num_packs_per_player
    cards = load_cube(Path(cube_path))
    total_needed = total_packs * pack_size
    draftable = len(cards)
    if total_needed > draftable:
        raise click.ClickException(
            f"Not enough cards: need {total_needed} but cube has {draftable} draftable cards."
        )

    if show_cards:
        categorized = categorize_cards(cards)
        card_packs = generate_card_packs(categorized, total_packs, pack_size)
        output = _format_card_packs(card_packs, players, num_packs_per_player)
    else:
        templates = generate_pack_templates(total_packs, pack_size)
        output = _format_templates(templates, players, num_packs_per_player)

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for player_idx in range(players):
            player_file = out / f"player-{player_idx + 1}.txt"
            player_output = _format_player_section(
                player_idx, players, num_packs_per_player, pack_size,
                show_cards, templates if not show_cards else None,
                card_packs if show_cards else None,
            )
            player_file.write_text(player_output)
        click.echo(f"Packs written to {output_dir}/")
    else:
        click.echo(output)


def _format_templates(templates, players, packs_per_player):
    lines = []
    for player_idx in range(players):
        lines.append(f"=== Player {player_idx + 1} ===")
        for pack_idx in range(packs_per_player):
            t = templates[player_idx * packs_per_player + pack_idx]
            parts = []
            for color, abbr in [("white", "W"), ("blue", "U"), ("black", "B"),
                                ("red", "R"), ("green", "G")]:
                count = getattr(t, color)
                if count > 0:
                    parts.append(f"{count}{abbr}")
            if t.colorless:
                parts.append(f"{t.colorless}colorless")
            if t.multicolor:
                parts.append(f"{t.multicolor}multi")
            if t.land:
                parts.append(f"{t.land}land")
            if t.fixing:
                parts.append(f"{t.fixing}fixing")
            lines.append(f"  Pack {pack_idx + 1}:  {'  '.join(parts)}")
        lines.append("")
    return "\n".join(lines)


def _format_card_packs(card_packs, players, packs_per_player):
    lines = []
    for player_idx in range(players):
        lines.append(f"=== Player {player_idx + 1} ===")
        for pack_idx in range(packs_per_player):
            pack = card_packs[player_idx * packs_per_player + pack_idx]
            lines.append(f"  Pack {pack_idx + 1}:")
            for card in sorted(pack, key=lambda c: (c.colors or [""], c.name)):
                color_str = "/".join(c[0] for c in card.colors) if card.colors else "C"
                lines.append(f"    [{color_str}] {card.name}")
        lines.append("")
    return "\n".join(lines)


def _format_player_section(player_idx, players, packs_per_player, pack_size,
                           show_cards, templates, card_packs):
    lines = [f"Player {player_idx + 1}", ""]
    for pack_idx in range(packs_per_player):
        idx = player_idx * packs_per_player + pack_idx
        if show_cards:
            pack = card_packs[idx]
            lines.append(f"Pack {pack_idx + 1}:")
            for card in sorted(pack, key=lambda c: (c.colors or [""], c.name)):
                color_str = "/".join(c[0] for c in card.colors) if card.colors else "C"
                lines.append(f"  [{color_str}] {card.name}")
        else:
            t = templates[idx]
            parts = []
            for color, abbr in [("white", "W"), ("blue", "U"), ("black", "B"),
                                ("red", "R"), ("green", "G")]:
                count = getattr(t, color)
                if count > 0:
                    parts.append(f"{count}{abbr}")
            if t.colorless:
                parts.append(f"{t.colorless}colorless")
            if t.multicolor:
                parts.append(f"{t.multicolor}multi")
            if t.land:
                parts.append(f"{t.land}land")
            if t.fixing:
                parts.append(f"{t.fixing}fixing")
            lines.append(f"Pack {pack_idx + 1}:  {'  '.join(parts)}")
        lines.append("")
    return "\n".join(lines)
```

**Step 2: Test CLI manually**

Run: `cube-utils packs --cube cube-2.csv`
Expected: Template output showing pack breakdowns for 8 players, 3 packs each.

Run: `cube-utils packs --cube cube-2.csv --cards --players 2 --packs 1 --pack-size 9`
Expected: Card name output for 2 players, 1 pack each.

**Step 3: Commit**

```bash
git add src/cube_utils/cli.py
git commit --no-gpg-sign -m "feat: packs CLI command with template and cards modes"
```

---

## Summary

| Task | Description | Dependencies |
|------|-------------|--------------|
| 1 | Project scaffolding | — |
| 2 | Card data model + CSV loading | 1 |
| 3 | Card categorization | 2 |
| 4 | Scryfall enrichment | 2 |
| 5 | Theme detection | 2 |
| 6 | Color pair + bridge analysis | 5 |
| 7 | Guide markdown output + CLI | 6 |
| 8 | Review guide output, iterate | 7 |
| 9 | Write draft guide | 8 |
| 10 | Pack structure definitions | 3 |
| 11 | Pack template generation | 10 |
| 12 | Pack cards generation | 11 |
| 13 | Packs CLI command | 12 |
