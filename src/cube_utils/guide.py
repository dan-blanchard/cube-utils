"""Draft guide generation: theme detection, color pair analysis, and markdown output."""

from __future__ import annotations

from enum import Enum

from cube_utils.cards import Card


class Theme(Enum):
    """Detectable draft themes/archetypes."""

    SACRIFICE = "sacrifice"
    COUNTERS = "counters"
    ETB = "etb"
    SPELLS_MATTER = "spells_matter"
    TOKENS = "tokens"
    ARTIFACTS = "artifacts"
    BLINK = "blink"
    HEROIC = "heroic"
    CYCLING = "cycling"
    EQUIPMENT = "equipment"
    GRAVEYARD = "graveyard"
    AGGRO = "aggro"
    EVASION = "evasion"
    RAMP = "ramp"


THEME_PATTERNS: dict[Theme, dict[str, list[str]]] = {
    Theme.SACRIFICE: {
        "text": [
            "sacrifice a",
            "sacrifice this",
            "when this creature dies",
            "whenever a creature dies",
            "whenever a creature you control dies",
        ],
        "keywords": [],
    },
    Theme.COUNTERS: {
        "text": ["+1/+1 counter", "modular", "-1/-1 counter"],
        "keywords": [],
    },
    Theme.ETB: {
        "text": [
            "when this creature enters",
            "when this artifact enters",
            "when this enchantment enters",
            "when it enters",
            "enters the battlefield",
            "enters, ",
        ],
        "keywords": [],
    },
    Theme.SPELLS_MATTER: {
        "text": [
            "noncreature spell",
            "instant or sorcery",
            "prowess",
            "magecraft",
        ],
        "keywords": ["Prowess"],
    },
    Theme.TOKENS: {
        "text": ["create a", "create two", "creature token", "artifact token"],
        "keywords": [],
    },
    Theme.ARTIFACTS: {
        "text": [
            "artifact you control",
            "target artifact",
            "historic",
            "whenever you cast an artifact",
        ],
        "keywords": [],
    },
    Theme.BLINK: {
        "text": [
            "exile target creature you control, then return",
            "exile it, then return",
            "flicker",
        ],
        "keywords": [],
    },
    Theme.HEROIC: {
        "text": [
            "heroic",
            "whenever you cast a spell that targets",
            "target creature you control gets",
            "target creature gets +",
        ],
        "keywords": ["Heroic"],
    },
    Theme.CYCLING: {
        "text": [
            "cycling",
            "discard a card",
            "discard this card",
            "whenever you cycle",
            "whenever you discard",
        ],
        "keywords": ["Cycling"],
    },
    Theme.EQUIPMENT: {
        "text": ["equip ", "equipped creature", "attach"],
        "keywords": ["Equip"],
    },
    Theme.GRAVEYARD: {
        "text": [
            "return target creature card from your graveyard",
            "return target card from your graveyard",
            "from your graveyard to your hand",
            "from your graveyard to the battlefield",
            "escape",
            "embalm",
            "unearth",
            "flashback",
        ],
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
        "text": [
            "search your library for a basic land",
            "add one mana",
            "mana of any color",
            "put that card onto the battlefield",
        ],
        "keywords": [],
    },
}


def _card_matches_theme(card: Card, patterns: dict[str, list[str]]) -> bool:
    """Check if a card matches any text pattern or keyword for a theme."""
    text_lower = card.text.lower()
    for pattern in patterns.get("text", []):
        if pattern.lower() in text_lower:
            return True
    for keyword in patterns.get("keywords", []):
        if keyword in card.keywords:
            return True
    return False


def detect_themes(cards: list[Card]) -> dict[Theme, list[Card]]:
    """Detect which cards belong to each theme.

    A card can belong to multiple themes if it matches patterns for each.

    Args:
        cards: List of Card objects to analyze.

    Returns:
        Dict mapping each Theme to its list of matching cards.
    """
    result: dict[Theme, list[Card]] = {theme: [] for theme in Theme}
    for card in cards:
        for theme, patterns in THEME_PATTERNS.items():
            if _card_matches_theme(card, patterns):
                result[theme].append(card)
    return result
