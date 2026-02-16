"""Draft guide generation: theme detection, color pair analysis, and markdown output."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from itertools import combinations

from cube_utils.cards import Card


class Theme(Enum):
    """Detectable draft themes/archetypes."""

    REMOVAL = "removal"
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
    AGGRO = "aggro"
    RAMP = "ramp"
    EVASION = "evasion"


# Theme detection rules: each theme has three layers of detection.
# - "tags": Scryfall oracle tags (functional_tags on Card) -- primary signal
# - "keywords": Scryfall keyword abilities -- secondary signal
# - "text": Card text patterns -- fallback for cube-specific themes
THEME_PATTERNS: dict[Theme, dict[str, list[str]]] = {
    Theme.REMOVAL: {
        "tags": ["removal", "board-wipe", "burn", "bounce"],
        "keywords": [],
        "text": [],
    },
    Theme.SACRIFICE: {
        "tags": ["sacrifice-outlet"],
        "keywords": [],
        "text": [],
    },
    Theme.COUNTERS: {
        "tags": [],
        "keywords": [],
        "text": ["+1/+1 counter", "modular", "-1/-1 counter"],
    },
    Theme.ETB: {
        "tags": [],
        "keywords": [],
        "text": [
            "when this creature enters",
            "when this artifact enters",
            "when this enchantment enters",
            "when it enters",
        ],
    },
    Theme.SPELLS_MATTER: {
        "tags": [],
        "keywords": ["Prowess"],
        "text": [
            "noncreature spell",
            "instant or sorcery",
            "magecraft",
        ],
    },
    Theme.TOKENS: {
        "tags": [],
        "keywords": [],
        "text": [
            "creature token",
            "artifact token",
            "create a",
            "create two",
        ],
    },
    Theme.ARTIFACTS: {
        "tags": [],
        "keywords": [],
        "text": [
            "artifact you control",
            "target artifact",
            "historic",
            "whenever you cast an artifact",
        ],
    },
    Theme.BLINK: {
        "tags": ["flicker"],
        "keywords": [],
        "text": [],
    },
    Theme.HEROIC: {
        "tags": [],
        "keywords": ["Heroic"],
        "text": [
            "heroic",
            "whenever you cast a spell that targets",
            "target creature you control gets",
            "target creature gets +",
        ],
    },
    Theme.CYCLING: {
        "tags": ["discard-outlet"],
        "keywords": ["Cycling"],
        "text": [],
    },
    Theme.EQUIPMENT: {
        "tags": [],
        "keywords": ["Equip"],
        "text": ["equipped creature"],
    },
    Theme.GRAVEYARD: {
        "tags": ["recursion"],
        "keywords": ["Escape", "Embalm", "Unearth", "Flashback"],
        "text": [],
    },
    Theme.AGGRO: {
        "tags": [],
        "keywords": ["Haste"],
        "text": [],
    },
    Theme.RAMP: {
        "tags": ["ramp", "mana-dork"],
        "keywords": [],
        "text": [],
    },
    Theme.EVASION: {
        "tags": ["evasion"],
        "keywords": [],
        "text": [],
    },
}

# ETB exclusion patterns: lands entering tapped should not trigger ETB theme
_ETB_EXCLUDE_PATTERN = "enters the battlefield tapped"


def _card_matches_theme(
    *, card: Card, theme: Theme, patterns: dict[str, list[str]]
) -> bool:
    """Check if a card matches any tag, keyword, or text pattern for a theme.

    Uses a three-layer approach:
    1. Primary: functional_tags from Scryfall oracle tagger
    2. Secondary: keywords from Scryfall bulk data
    3. Fallback: text pattern matching
    """
    # Layer 1: Scryfall oracle tags (most reliable)
    for tag in patterns.get("tags", []):
        if tag in card.functional_tags:
            return True

    # Layer 2: Scryfall keywords
    for keyword in patterns.get("keywords", []):
        if keyword in card.keywords:
            return True

    # Layer 3: Text pattern matching (fallback)
    text_lower = card.text.lower()
    for pattern in patterns.get("text", []):
        if pattern.lower() in text_lower:
            # Exclude lands that just enter tapped from the ETB theme
            if (
                theme == Theme.ETB
                and _ETB_EXCLUDE_PATTERN in text_lower
                and card.is_land
            ):
                continue
            return True

    # Layer 1b: Cards that produce mana and aren't lands are ramp-adjacent
    return theme == Theme.RAMP and bool(card.produced_mana) and not card.is_land


def detect_themes(cards: list[Card]) -> dict[Theme, list[Card]]:
    """Detect which cards belong to each theme.

    Uses a hybrid approach: primary detection via Scryfall oracle tags,
    secondary via keywords, fallback via text patterns.

    A card can belong to multiple themes if it matches patterns for each.

    Args:
        cards: List of Card objects to analyze.

    Returns:
        Dict mapping each Theme to its list of matching cards.
    """
    result: dict[Theme, list[Card]] = {theme: [] for theme in Theme}
    for card in cards:
        for theme, patterns in THEME_PATTERNS.items():
            if _card_matches_theme(card=card, theme=theme, patterns=patterns):
                result[theme].append(card)
    return result


# --- Color Pair Analysis ---

_COLOR_ABBREV = {
    "White": "W",
    "Blue": "U",
    "Black": "B",
    "Red": "R",
    "Green": "G",
}

_GUILD_NAMES = {
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

_ALL_COLORS = ["Black", "Blue", "Green", "Red", "White"]
COLOR_PAIRS: list[tuple[str, str]] = [(a, b) for a, b in combinations(_ALL_COLORS, 2)]


@dataclass
class ColorPairAnalysis:
    """Analysis of a two-color pair in the cube."""

    colors: tuple[str, str]
    multicolor_cards: list[Card]
    shared_themes: list[Theme]
    theme_cards: dict[Theme, list[Card]] = field(default_factory=dict)


def analyze_color_pairs(
    cards: list[Card], themes: dict[Theme, list[Card]]
) -> list[ColorPairAnalysis]:
    """Analyze each two-color pair for multicolor cards and shared themes.

    Args:
        cards: List of all cube cards.
        themes: Dict of detected themes from detect_themes().

    Returns:
        List of ColorPairAnalysis, one per color pair.
    """
    results: list[ColorPairAnalysis] = []

    for pair in COLOR_PAIRS:
        pair_set = set(pair)

        # Find multicolor cards whose colors exactly match this pair
        multicolor = [c for c in cards if c.is_multicolor and set(c.colors) == pair_set]

        # Find themes where both colors contribute cards
        shared: list[Theme] = []
        theme_card_map: dict[Theme, list[Card]] = {}
        for theme, theme_cards in themes.items():
            colors_present = set()
            cards_in_pair: list[Card] = []
            for tc in theme_cards:
                card_colors = set(tc.colors)
                if card_colors & pair_set:
                    colors_present |= card_colors & pair_set
                    cards_in_pair.append(tc)
            if pair_set <= colors_present:
                shared.append(theme)
                theme_card_map[theme] = cards_in_pair

        results.append(
            ColorPairAnalysis(
                colors=pair,
                multicolor_cards=multicolor,
                shared_themes=shared,
                theme_cards=theme_card_map,
            )
        )

    return results


def find_bridge_cards(themes: dict[Theme, list[Card]]) -> list[Card]:
    """Find cards that appear in two or more themes.

    Args:
        themes: Dict of detected themes from detect_themes().

    Returns:
        List of unique cards appearing in 2+ themes, sorted by name.
    """
    card_theme_count: Counter[str] = Counter()
    card_by_name: dict[str, Card] = {}

    for theme_cards in themes.values():
        for card in theme_cards:
            card_theme_count[card.name] += 1
            card_by_name[card.name] = card

    bridges = [
        card_by_name[name] for name, count in card_theme_count.items() if count >= 2
    ]
    return sorted(bridges, key=lambda c: c.name)


# --- Guide Markdown Output ---


def _format_theme_name(theme: Theme) -> str:
    """Format a Theme enum value as a title-cased string."""
    return theme.name.replace("_", " ").title()


def _get_guild_name(pair: tuple[str, str]) -> str:
    """Get the guild name for a color pair."""
    key = tuple(sorted(pair))
    return _GUILD_NAMES.get(key, f"{pair[0]}/{pair[1]}")


def _get_color_abbrev(color: str) -> str:
    """Get the single-letter abbreviation for a color."""
    return _COLOR_ABBREV.get(color, color[0])


def _themes_for_card(card: Card, themes: dict[Theme, list[Card]]) -> list[Theme]:
    """Return the list of themes a card belongs to."""
    return [theme for theme, cards in themes.items() if card in cards]


def generate_guide_markdown(
    *,
    themes: dict[Theme, list[Card]],
    pairs: list[ColorPairAnalysis],
    bridges: list[Card],
) -> str:
    """Generate a draft guide skeleton in Markdown format.

    Args:
        themes: Dict of detected themes.
        pairs: List of color pair analyses.
        bridges: List of bridge cards.

    Returns:
        Markdown string with the complete draft guide.
    """
    lines: list[str] = []

    lines.append("# Draft Guide Skeleton")
    lines.append("")

    # Themes section
    lines.append("## Themes")
    lines.append("")
    for theme in Theme:
        theme_cards = themes.get(theme, [])
        if not theme_cards:
            continue
        lines.append(f"### {_format_theme_name(theme)}")
        lines.append("")

        # Group cards by color
        color_groups: dict[str, list[Card]] = {}
        for card in theme_cards:
            if card.is_multicolor:
                key = "/".join(_get_color_abbrev(c) for c in sorted(card.colors))
            elif card.is_colorless:
                key = "Colorless"
            else:
                key = card.colors[0] if card.colors else "Colorless"
            color_groups.setdefault(key, []).append(card)

        for color_key in sorted(color_groups.keys()):
            lines.append(
                f"**{color_key}:** {', '.join(c.name for c in color_groups[color_key])}"
            )
            lines.append("")

    # Color Pairs section
    lines.append("## Color Pairs")
    lines.append("")
    for pair_analysis in pairs:
        guild = _get_guild_name(pair_analysis.colors)
        abbrevs = "/".join(_get_color_abbrev(c) for c in pair_analysis.colors)
        lines.append(f"### {guild} ({abbrevs})")
        lines.append("")

        if pair_analysis.multicolor_cards:
            gold_names = ", ".join(c.name for c in pair_analysis.multicolor_cards)
            lines.append(f"**Gold cards:** {gold_names}")
            lines.append("")

        if pair_analysis.shared_themes:
            theme_names = ", ".join(
                _format_theme_name(t) for t in pair_analysis.shared_themes
            )
            lines.append(f"**Shared themes:** {theme_names}")
            lines.append("")

            for theme in pair_analysis.shared_themes:
                cards_for_theme = pair_analysis.theme_cards.get(theme, [])
                if cards_for_theme:
                    card_names = ", ".join(c.name for c in cards_for_theme)
                    lines.append(f"- {_format_theme_name(theme)}: {card_names}")
            lines.append("")

    # Bridge Cards section
    lines.append("## Bridge Cards")
    lines.append("")
    if bridges:
        for card in bridges:
            card_themes = _themes_for_card(card, themes)
            theme_names = ", ".join(_format_theme_name(t) for t in card_themes)
            lines.append(f"- **{card.name}**: {theme_names}")
        lines.append("")

    return "\n".join(lines)
