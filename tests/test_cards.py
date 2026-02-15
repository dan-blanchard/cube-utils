"""Tests for Card data model and CSV loading."""

from pathlib import Path

from cube_utils.cards import Card, load_cube


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
