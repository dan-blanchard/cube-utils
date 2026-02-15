"""Tests for Card data model and CSV loading."""

from pathlib import Path

from cube_utils.cards import (
    Card,
    Category,
    categorize_cards,
    enrich_with_scryfall,
    enrich_with_tags,
    load_cube,
)


class TestCard:
    """Tests for the Card dataclass."""

    def test_card_creation(self):
        card = Card(
            name="Lightning Bolt",
            colors=["Red"],
            cmc=1,
            scryfall_id="e3285e6b-3e79-4d7c-bf96-d920f973b122",
            types=["Instant"],
            text="Lightning Bolt deals 3 damage to any target.",
        )
        assert card.name == "Lightning Bolt"
        assert card.colors == ["Red"]
        assert card.cmc == 1
        assert card.keywords == []

    def test_is_multicolor(self):
        card = Card(
            name="Anax and Cymede",
            colors=["White", "Red"],
            cmc=3,
            scryfall_id="abc",
            types=["Creature"],
            text="",
        )
        assert card.is_multicolor is True

    def test_is_not_multicolor(self):
        card = Card(
            name="Lightning Bolt",
            colors=["Red"],
            cmc=1,
            scryfall_id="abc",
            types=["Instant"],
            text="",
        )
        assert card.is_multicolor is False

    def test_is_colorless(self):
        card = Card(
            name="Chromatic Sphere",
            colors=[],
            cmc=1,
            scryfall_id="abc",
            types=["Artifact"],
            text="",
        )
        assert card.is_colorless is True

    def test_is_not_colorless(self):
        card = Card(
            name="Lightning Bolt",
            colors=["Red"],
            cmc=1,
            scryfall_id="abc",
            types=["Instant"],
            text="",
        )
        assert card.is_colorless is False

    def test_is_land(self):
        card = Card(
            name="Evolving Wilds",
            colors=[],
            cmc=0,
            scryfall_id="abc",
            types=["Land"],
            text="",
        )
        assert card.is_land is True

    def test_is_not_land_if_colored(self):
        """A colored card with Land type should not be is_land (requires colorless)."""
        card = Card(
            name="Dryad Arbor",
            colors=["Green"],
            cmc=0,
            scryfall_id="abc",
            types=["Land", "Creature"],
            text="",
        )
        assert card.is_land is False

    def test_is_token(self):
        card = Card(
            name="Goblin",
            colors=["Red"],
            cmc=0,
            scryfall_id="abc",
            types=["Creature", "Token"],
            text="",
        )
        assert card.is_token is True

    def test_is_not_token(self):
        card = Card(
            name="Lightning Bolt",
            colors=["Red"],
            cmc=1,
            scryfall_id="abc",
            types=["Instant"],
            text="",
        )
        assert card.is_token is False

    def test_is_draftable(self):
        card = Card(
            name="Lightning Bolt",
            colors=["Red"],
            cmc=1,
            scryfall_id="abc",
            types=["Instant"],
            text="",
        )
        assert card.is_draftable is True

    def test_token_not_draftable(self):
        card = Card(
            name="Goblin",
            colors=["Red"],
            cmc=0,
            scryfall_id="abc",
            types=["Creature", "Token"],
            text="",
        )
        assert card.is_draftable is False

    def test_card_type_not_draftable(self):
        card = Card(
            name="On an Adventure",
            colors=[],
            cmc=0,
            scryfall_id="abc",
            types=["Card"],
            text="",
        )
        assert card.is_draftable is False


class TestLoadCube:
    """Tests for the load_cube function."""

    def test_returns_list_of_cards(self, sample_csv: Path):
        cards = load_cube(sample_csv)
        assert isinstance(cards, list)
        assert all(isinstance(c, Card) for c in cards)

    def test_excludes_tokens(self, sample_csv: Path):
        cards = load_cube(sample_csv)
        names = [c.name for c in cards]
        assert "Goblin" not in names

    def test_excludes_card_type(self, sample_csv: Path):
        cards = load_cube(sample_csv)
        names = [c.name for c in cards]
        assert "On an Adventure" not in names

    def test_includes_draftable_cards(self, sample_csv: Path):
        cards = load_cube(sample_csv)
        names = [c.name for c in cards]
        assert "Lightning Bolt" in names
        assert "Counterspell" in names
        assert "Evolving Wilds" in names

    def test_parses_fields_correctly(self, sample_csv: Path):
        cards = load_cube(sample_csv)
        bolt = next(c for c in cards if c.name == "Lightning Bolt")
        assert bolt.colors == ["Red"]
        assert bolt.cmc == 1
        assert bolt.scryfall_id == "e3285e6b-3e79-4d7c-bf96-d920f973b122"
        assert bolt.types == ["Instant"]
        assert "3 damage" in bolt.text

    def test_handles_multicolor(self, sample_csv: Path):
        cards = load_cube(sample_csv)
        anax = next(c for c in cards if c.name == "Anax and Cymede")
        assert anax.colors == ["White", "Red"]
        assert anax.is_multicolor is True

    def test_handles_colorless(self, sample_csv: Path):
        cards = load_cube(sample_csv)
        sphere = next(c for c in cards if c.name == "Chromatic Sphere")
        assert sphere.colors == []
        assert sphere.is_colorless is True

    def test_expected_count(self, sample_csv: Path):
        """Sample CSV has 9 rows: 7 draftable + 1 token + 1 Card type."""
        cards = load_cube(sample_csv)
        assert len(cards) == 7

    def test_real_cube_excludes_tokens(self, real_cube_path: Path):
        """Integration test: real cube file should have no tokens."""
        if not real_cube_path.exists():
            pytest.skip("Real cube CSV not available")
        cards = load_cube(real_cube_path)
        for card in cards:
            assert "Token" not in card.types, f"{card.name} is a token"
            assert "Card" not in card.types, f"{card.name} is a Card type"
        # Should have roughly 442 draftable cards (465 - 23 non-draftable)
        assert len(cards) > 400


class TestCategorizeCards:
    """Tests for the categorize_cards function."""

    def _make_card(self, name="Test", colors=None, types=None, text=""):
        return Card(
            name=name,
            colors=colors or [],
            cmc=1,
            scryfall_id="abc",
            types=types or ["Creature"],
            text=text,
        )

    def test_mono_white(self):
        card = self._make_card(colors=["White"])
        result = categorize_cards([card])
        assert result[Category.MONO_WHITE] == [card]

    def test_mono_blue(self):
        card = self._make_card(colors=["Blue"])
        result = categorize_cards([card])
        assert result[Category.MONO_BLUE] == [card]

    def test_mono_black(self):
        card = self._make_card(colors=["Black"])
        result = categorize_cards([card])
        assert result[Category.MONO_BLACK] == [card]

    def test_mono_red(self):
        card = self._make_card(colors=["Red"])
        result = categorize_cards([card])
        assert result[Category.MONO_RED] == [card]

    def test_mono_green(self):
        card = self._make_card(colors=["Green"])
        result = categorize_cards([card])
        assert result[Category.MONO_GREEN] == [card]

    def test_multicolor(self):
        card = self._make_card(colors=["White", "Red"])
        result = categorize_cards([card])
        assert result[Category.MULTICOLOR] == [card]

    def test_land(self):
        card = self._make_card(types=["Land"])
        result = categorize_cards([card])
        assert result[Category.LAND] == [card]

    def test_fixing_mana_of_any_color(self):
        card = self._make_card(
            types=["Artifact"],
            text="Add one mana of any color.",
        )
        result = categorize_cards([card])
        assert result[Category.FIXING] == [card]

    def test_fixing_search_basic_land(self):
        card = self._make_card(
            types=["Artifact"],
            text="Search your library for a basic land card.",
        )
        result = categorize_cards([card])
        assert result[Category.FIXING] == [card]

    def test_fixing_add_one_mana(self):
        card = self._make_card(
            types=["Artifact"],
            text="Add one mana of the chosen color.",
        )
        result = categorize_cards([card])
        assert result[Category.FIXING] == [card]

    def test_colorless(self):
        card = self._make_card(
            types=["Artifact"],
            text="Equipped creature gets +1/+1.",
        )
        result = categorize_cards([card])
        assert result[Category.COLORLESS] == [card]

    def test_every_card_categorized_exactly_once(self, sample_csv):
        cards = load_cube(sample_csv)
        result = categorize_cards(cards)
        all_categorized = []
        for cat_cards in result.values():
            all_categorized.extend(cat_cards)
        assert len(all_categorized) == len(cards)
        # No duplicates
        assert len(set(id(c) for c in all_categorized)) == len(cards)


class TestEnrichWithScryfall:
    """Tests for the enrich_with_scryfall function."""

    def test_enrichment_adds_keywords(self, sample_csv, sample_scryfall_path):
        cards = load_cube(sample_csv)
        enrich_with_scryfall(cards, sample_scryfall_path)
        bolt = next(c for c in cards if c.name == "Lightning Bolt")
        assert bolt.keywords == ["Prowess"]

    def test_enrichment_adds_empty_keywords(self, sample_csv, sample_scryfall_path):
        cards = load_cube(sample_csv)
        enrich_with_scryfall(cards, sample_scryfall_path)
        counterspell = next(c for c in cards if c.name == "Counterspell")
        assert counterspell.keywords == []

    def test_enrichment_multicolor_card(self, sample_csv, sample_scryfall_path):
        cards = load_cube(sample_csv)
        enrich_with_scryfall(cards, sample_scryfall_path)
        anax = next(c for c in cards if c.name == "Anax and Cymede")
        assert anax.keywords == ["Heroic"]

    def test_skips_cards_not_in_scryfall(self, sample_csv, sample_scryfall_path):
        """Cards whose scryfall_id is not in the JSON should keep empty keywords."""
        cards = load_cube(sample_csv)
        enrich_with_scryfall(cards, sample_scryfall_path)
        # Evolving Wilds is not in the sample scryfall data
        ew = next(c for c in cards if c.name == "Evolving Wilds")
        assert ew.keywords == []

    def test_only_loads_cube_card_ids(self, sample_csv, sample_scryfall_path):
        """The lookup dict should only contain IDs present in the cube."""
        cards = load_cube(sample_csv)
        enrich_with_scryfall(cards, sample_scryfall_path)
        # "Some Other Card" (aaaaaaaa-...) should not affect any cube card
        for card in cards:
            assert "Flying" not in card.keywords or card.name != "Some Other Card"

    def test_enrichment_adds_oracle_id(self, sample_csv, sample_scryfall_path):
        cards = load_cube(sample_csv)
        enrich_with_scryfall(cards, sample_scryfall_path)
        bolt = next(c for c in cards if c.name == "Lightning Bolt")
        assert bolt.oracle_id == "orc-bolt"

    def test_enrichment_adds_produced_mana(self, sample_csv, sample_scryfall_path):
        cards = load_cube(sample_csv)
        enrich_with_scryfall(cards, sample_scryfall_path)
        sphere = next(c for c in cards if c.name == "Chromatic Sphere")
        assert sphere.produced_mana == ["W", "U", "B", "R", "G"]

    def test_enrichment_empty_produced_mana(self, sample_csv, sample_scryfall_path):
        cards = load_cube(sample_csv)
        enrich_with_scryfall(cards, sample_scryfall_path)
        bolt = next(c for c in cards if c.name == "Lightning Bolt")
        assert bolt.produced_mana == []

    def test_unenriched_card_has_empty_oracle_id(self, sample_csv, sample_scryfall_path):
        cards = load_cube(sample_csv)
        enrich_with_scryfall(cards, sample_scryfall_path)
        ew = next(c for c in cards if c.name == "Evolving Wilds")
        assert ew.oracle_id == ""


class TestEnrichWithTags:
    """Tests for the enrich_with_tags function."""

    def test_adds_functional_tags(self, sample_csv, sample_scryfall_path, sample_tags_cache):
        cards = load_cube(sample_csv)
        enrich_with_scryfall(cards, sample_scryfall_path)
        enrich_with_tags(cards, sample_tags_cache)
        bolt = next(c for c in cards if c.name == "Lightning Bolt")
        assert "burn" in bolt.functional_tags
        assert "removal" in bolt.functional_tags

    def test_card_with_no_oracle_id_gets_no_tags(self, sample_csv, sample_scryfall_path, sample_tags_cache):
        cards = load_cube(sample_csv)
        enrich_with_scryfall(cards, sample_scryfall_path)
        enrich_with_tags(cards, sample_tags_cache)
        ew = next(c for c in cards if c.name == "Evolving Wilds")
        assert ew.functional_tags == []

    def test_card_not_in_any_tag(self, sample_csv, sample_scryfall_path, sample_tags_cache):
        cards = load_cube(sample_csv)
        enrich_with_scryfall(cards, sample_scryfall_path)
        enrich_with_tags(cards, sample_tags_cache)
        anax = next(c for c in cards if c.name == "Anax and Cymede")
        assert anax.functional_tags == []

    def test_multiple_tags_on_one_card(self, sample_csv, sample_scryfall_path, sample_tags_cache):
        cards = load_cube(sample_csv)
        enrich_with_scryfall(cards, sample_scryfall_path)
        enrich_with_tags(cards, sample_tags_cache)
        counterspell = next(c for c in cards if c.name == "Counterspell")
        assert "removal" in counterspell.functional_tags
        assert "counterspell" in counterspell.functional_tags
