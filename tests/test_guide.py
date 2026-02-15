"""Tests for draft guide generation: themes, color pairs, bridges, markdown."""

from cube_utils.cards import Card
from cube_utils.guide import (
    Theme,
    detect_themes,
)


def _make_card(
    name="Test",
    colors=None,
    types=None,
    text="",
    keywords=None,
    cmc=1,
):
    return Card(
        name=name,
        colors=colors or [],
        cmc=cmc,
        scryfall_id="abc",
        types=types or ["Creature"],
        text=text,
        keywords=keywords or [],
    )


# --- Task 5: Theme Detection ---


class TestDetectThemes:
    """Tests for detect_themes."""

    def test_detect_sacrifice_theme(self):
        card = _make_card(
            name="Viscera Seer",
            colors=["Black"],
            text="Sacrifice a creature: Scry 1.",
        )
        themes = detect_themes([card])
        assert card in themes[Theme.SACRIFICE]

    def test_detect_counters_theme(self):
        card = _make_card(
            name="Arcbound Ravager",
            colors=[],
            types=["Artifact", "Creature"],
            text="Sacrifice an artifact: Put a +1/+1 counter on Arcbound Ravager. Modular 1",
        )
        themes = detect_themes([card])
        assert card in themes[Theme.COUNTERS]

    def test_detect_etb_theme(self):
        card = _make_card(
            name="Mulldrifter",
            colors=["Blue"],
            text="When this creature enters the battlefield, draw two cards.",
        )
        themes = detect_themes([card])
        assert card in themes[Theme.ETB]

    def test_detect_spells_matter_via_text(self):
        card = _make_card(
            name="Young Pyromancer",
            colors=["Red"],
            text="Whenever you cast a noncreature spell, create a 1/1 red Elemental creature token.",
        )
        themes = detect_themes([card])
        assert card in themes[Theme.SPELLS_MATTER]

    def test_detect_spells_matter_via_keyword(self):
        card = _make_card(
            name="Monastery Swiftspear",
            colors=["Red"],
            text="Haste",
            keywords=["Prowess", "Haste"],
        )
        themes = detect_themes([card])
        assert card in themes[Theme.SPELLS_MATTER]

    def test_card_in_multiple_themes(self):
        """A card can belong to multiple themes."""
        card = _make_card(
            name="Arcbound Ravager",
            colors=[],
            types=["Artifact", "Creature"],
            text="Sacrifice an artifact: Put a +1/+1 counter on Arcbound Ravager. Modular 1",
        )
        themes = detect_themes([card])
        assert card in themes[Theme.SACRIFICE]
        assert card in themes[Theme.COUNTERS]

    def test_detect_tokens_theme(self):
        card = _make_card(
            name="Raise the Alarm",
            colors=["White"],
            text="Create two 1/1 white Soldier creature tokens.",
        )
        themes = detect_themes([card])
        assert card in themes[Theme.TOKENS]

    def test_detect_equipment_via_keyword(self):
        card = _make_card(
            name="Bonesplitter",
            colors=[],
            types=["Artifact"],
            text="Equipped creature gets +2/+0. Equip {1}",
            keywords=["Equip"],
        )
        themes = detect_themes([card])
        assert card in themes[Theme.EQUIPMENT]

    def test_no_false_positive(self):
        card = _make_card(
            name="Grizzly Bears",
            colors=["Green"],
            text="",
        )
        themes = detect_themes([card])
        for theme_cards in themes.values():
            assert card not in theme_cards
