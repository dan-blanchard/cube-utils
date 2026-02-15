"""Tests for draft guide generation: themes, color pairs, bridges, markdown."""

from cube_utils.cards import Card
from cube_utils.guide import (
    ColorPairAnalysis,
    Theme,
    analyze_color_pairs,
    detect_themes,
    find_bridge_cards,
    generate_guide_markdown,
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


# --- Task 6: Color Pair Analysis and Bridge Cards ---


class TestAnalyzeColorPairs:
    """Tests for analyze_color_pairs."""

    def test_finds_multicolor_cards_for_pair(self):
        gold = _make_card(
            name="Anax and Cymede",
            colors=["White", "Red"],
            text="Heroic",
            keywords=["Heroic"],
        )
        mono = _make_card(name="Lightning Bolt", colors=["Red"], text="3 damage")
        themes = detect_themes([gold, mono])
        pairs = analyze_color_pairs([gold, mono], themes)

        # Find the Red/White (Boros) pair
        boros = next(p for p in pairs if set(p.colors) == {"Red", "White"})
        assert gold in boros.multicolor_cards
        assert mono not in boros.multicolor_cards

    def test_finds_shared_themes(self):
        white_heroic = _make_card(
            name="Favored Hoplite",
            colors=["White"],
            text="Heroic -- Whenever you cast a spell that targets Favored Hoplite",
            keywords=["Heroic"],
        )
        red_heroic = _make_card(
            name="Satyr Hoplite",
            colors=["Red"],
            text="Heroic -- Whenever you cast a spell that targets Satyr Hoplite",
            keywords=["Heroic"],
        )
        themes = detect_themes([white_heroic, red_heroic])
        pairs = analyze_color_pairs([white_heroic, red_heroic], themes)

        boros = next(p for p in pairs if set(p.colors) == {"Red", "White"})
        assert Theme.HEROIC in boros.shared_themes

    def test_no_shared_theme_if_only_one_color(self):
        red_aggro = _make_card(
            name="Goblin Guide",
            colors=["Red"],
            text="Haste",
            keywords=["Haste"],
        )
        themes = detect_themes([red_aggro])
        pairs = analyze_color_pairs([red_aggro], themes)

        # Boros should NOT have Aggro as shared since only Red contributes
        boros = next(p for p in pairs if set(p.colors) == {"Red", "White"})
        assert Theme.AGGRO not in boros.shared_themes

    def test_returns_ten_pairs(self):
        themes = detect_themes([])
        pairs = analyze_color_pairs([], themes)
        assert len(pairs) == 10


class TestFindBridgeCards:
    """Tests for find_bridge_cards."""

    def test_finds_bridge_card(self):
        # This card matches both SACRIFICE and COUNTERS
        card = _make_card(
            name="Arcbound Ravager",
            colors=[],
            types=["Artifact", "Creature"],
            text="Sacrifice an artifact: Put a +1/+1 counter on Arcbound Ravager. Modular 1",
        )
        themes = detect_themes([card])
        bridges = find_bridge_cards(themes)
        assert card.name in [c.name for c in bridges]

    def test_single_theme_card_not_bridge(self):
        card = _make_card(
            name="Viscera Seer",
            colors=["Black"],
            text="Sacrifice a creature: Scry 1.",
        )
        themes = detect_themes([card])
        bridges = find_bridge_cards(themes)
        assert card.name not in [c.name for c in bridges]

    def test_bridges_sorted_by_name(self):
        card_a = _make_card(
            name="Zealous Ravager",
            text="Sacrifice a creature. Put a +1/+1 counter on it.",
        )
        card_b = _make_card(
            name="Alpha Bridge",
            text="Sacrifice a creature. Put a +1/+1 counter on it.",
        )
        themes = detect_themes([card_a, card_b])
        bridges = find_bridge_cards(themes)
        names = [c.name for c in bridges]
        assert names == sorted(names)


# --- Task 7: Guide Markdown Output ---


class TestGenerateGuideMarkdown:
    """Tests for generate_guide_markdown."""

    def _build_guide_data(self):
        """Create a small set of cards and run the full pipeline."""
        sacrifice_card = _make_card(
            name="Viscera Seer",
            colors=["Black"],
            text="Sacrifice a creature: Scry 1.",
        )
        heroic_white = _make_card(
            name="Favored Hoplite",
            colors=["White"],
            text="Heroic",
            keywords=["Heroic"],
        )
        heroic_red = _make_card(
            name="Satyr Hoplite",
            colors=["Red"],
            text="Heroic",
            keywords=["Heroic"],
        )
        gold = _make_card(
            name="Anax and Cymede",
            colors=["White", "Red"],
            text="Heroic",
            keywords=["Heroic"],
        )
        bridge = _make_card(
            name="Arcbound Ravager",
            colors=[],
            types=["Artifact", "Creature"],
            text="Sacrifice an artifact: Put a +1/+1 counter on Arcbound Ravager.",
        )
        cards = [sacrifice_card, heroic_white, heroic_red, gold, bridge]
        themes = detect_themes(cards)
        pairs = analyze_color_pairs(cards, themes)
        bridges = find_bridge_cards(themes)
        return themes, pairs, bridges, cards

    def test_has_main_heading(self):
        themes, pairs, bridges, _ = self._build_guide_data()
        md = generate_guide_markdown(themes, pairs, bridges)
        assert "# Draft Guide Skeleton" in md

    def test_has_themes_section(self):
        themes, pairs, bridges, _ = self._build_guide_data()
        md = generate_guide_markdown(themes, pairs, bridges)
        assert "## Themes" in md

    def test_has_color_pairs_section(self):
        themes, pairs, bridges, _ = self._build_guide_data()
        md = generate_guide_markdown(themes, pairs, bridges)
        assert "## Color Pairs" in md

    def test_has_bridge_cards_section(self):
        themes, pairs, bridges, _ = self._build_guide_data()
        md = generate_guide_markdown(themes, pairs, bridges)
        assert "## Bridge Cards" in md

    def test_lists_card_names(self):
        themes, pairs, bridges, _ = self._build_guide_data()
        md = generate_guide_markdown(themes, pairs, bridges)
        assert "Viscera Seer" in md
        assert "Favored Hoplite" in md
        assert "Anax and Cymede" in md
        assert "Arcbound Ravager" in md

    def test_bridge_card_lists_themes(self):
        themes, pairs, bridges, _ = self._build_guide_data()
        md = generate_guide_markdown(themes, pairs, bridges)
        # Arcbound Ravager should be listed as a bridge with its themes
        assert "**Arcbound Ravager**" in md

    def test_guild_name_appears(self):
        themes, pairs, bridges, _ = self._build_guide_data()
        md = generate_guide_markdown(themes, pairs, bridges)
        assert "Boros" in md
