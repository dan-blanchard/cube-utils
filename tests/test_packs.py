"""Tests for pack generation."""

import csv
from pathlib import Path

import pytest
from click.testing import CliRunner

from cube_utils.cards import Card, categorize_cards
from cube_utils.cli import main
from cube_utils.packs import (
    PackTemplate,
    generate_card_packs,
    generate_grid_templates,
    generate_pack_templates,
    get_pack_structure,
    packs_to_templates,
)

# ---------------------------------------------------------------------------
# Task 10: PackStructure tests
# ---------------------------------------------------------------------------


class TestPackStructure:
    """Tests for PackStructure dataclass and get_pack_structure."""

    def test_pack_structure_15(self):
        ps = get_pack_structure(15)
        assert ps.mono_per_color == 1
        assert ps.colorless == 1
        assert ps.multicolor_range == (2, 3)
        assert ps.land_range == (2, 3)
        assert ps.fixing == 1
        assert ps.extra_mono == 3

    def test_pack_structure_11(self):
        ps = get_pack_structure(11)
        assert ps.mono_per_color == 1
        assert ps.colorless == 1
        assert ps.multicolor_range == (1, 2)
        assert ps.land_range == (1, 2)
        assert ps.fixing == 1
        assert ps.extra_mono == 1

    def test_pack_structure_9(self):
        ps = get_pack_structure(9)
        assert ps.mono_per_color == 1
        assert ps.colorless == 1
        assert ps.multicolor_range == (1, 1)
        assert ps.land_range == (1, 1)
        assert ps.fixing == 1
        assert ps.extra_mono == 0

    def test_invalid_pack_size(self):
        with pytest.raises(ValueError, match="Unsupported pack size"):
            get_pack_structure(12)

    def test_total_15(self):
        ps = get_pack_structure(15)
        assert ps.total() == 15

    def test_total_11(self):
        ps = get_pack_structure(11)
        assert ps.total() == 11

    def test_total_9(self):
        ps = get_pack_structure(9)
        assert ps.total() == 9

    def test_multi_land_complementary_15(self):
        """When multi is max, land is min and vice versa; total stays the same."""
        ps = get_pack_structure(15)
        # max multi + min land == min multi + max land
        assert (
            ps.multicolor_range[1] + ps.land_range[0]
            == ps.multicolor_range[0] + ps.land_range[1]
        )


# ---------------------------------------------------------------------------
# Task 11: PackTemplate tests
# ---------------------------------------------------------------------------


class TestPackTemplate:
    """Tests for PackTemplate dataclass."""

    def test_template_total(self):
        t = PackTemplate(
            white=2,
            blue=1,
            black=1,
            red=1,
            green=1,
            colorless=1,
            multicolor=3,
            land=2,
            fixing=1,
        )
        assert t.total() == 13  # 2+1+1+1+1+1+3+2+1

    def test_template_total_15(self):
        t = PackTemplate(
            white=2,
            blue=1,
            black=1,
            red=2,
            green=1,
            colorless=1,
            multicolor=2,
            land=3,
            fixing=1,
        )
        assert t.total() == 14  # wrong if we don't have correct values
        # Let's test a real 15-card template
        t2 = PackTemplate(
            white=2,
            blue=1,
            black=1,
            red=2,
            green=1,
            colorless=1,
            multicolor=3,
            land=2,
            fixing=2,
        )
        assert t2.total() == 15


class TestGeneratePackTemplates:
    """Tests for generate_pack_templates."""

    def test_returns_correct_count(self):
        templates = generate_pack_templates(num_packs=6, pack_size=15)
        assert len(templates) == 6

    def test_each_template_has_correct_total(self):
        templates = generate_pack_templates(num_packs=10, pack_size=15)
        for t in templates:
            assert t.total() == 15

    def test_each_template_has_correct_total_11(self):
        templates = generate_pack_templates(num_packs=10, pack_size=11)
        for t in templates:
            assert t.total() == 11

    def test_each_template_has_correct_total_9(self):
        templates = generate_pack_templates(num_packs=10, pack_size=9)
        for t in templates:
            assert t.total() == 9

    def test_each_color_at_least_1(self):
        templates = generate_pack_templates(num_packs=20, pack_size=15)
        for t in templates:
            assert t.white >= 1
            assert t.blue >= 1
            assert t.black >= 1
            assert t.red >= 1
            assert t.green >= 1

    def test_colorless_matches_structure(self):
        templates = generate_pack_templates(num_packs=10, pack_size=15)
        for t in templates:
            assert t.colorless == 1

    def test_fixing_matches_structure(self):
        templates = generate_pack_templates(num_packs=10, pack_size=15)
        for t in templates:
            assert t.fixing == 1

    def test_multicolor_within_range(self):
        ps = get_pack_structure(15)
        templates = generate_pack_templates(num_packs=50, pack_size=15)
        for t in templates:
            assert ps.multicolor_range[0] <= t.multicolor <= ps.multicolor_range[1]

    def test_land_within_range(self):
        ps = get_pack_structure(15)
        templates = generate_pack_templates(num_packs=50, pack_size=15)
        for t in templates:
            assert ps.land_range[0] <= t.land <= ps.land_range[1]

    def test_extra_mono_distributed(self):
        """For 15-card packs, extra_mono=3 means sum of colors is 5+3=8."""
        templates = generate_pack_templates(num_packs=10, pack_size=15)
        for t in templates:
            color_total = t.white + t.blue + t.black + t.red + t.green
            assert color_total == 8  # 5 base + 3 extra

    def test_extra_mono_for_11(self):
        """For 11-card packs, extra_mono=1 so sum of colors is 5+1=6."""
        templates = generate_pack_templates(num_packs=10, pack_size=11)
        for t in templates:
            color_total = t.white + t.blue + t.black + t.red + t.green
            assert color_total == 6  # 5 base + 1 extra


# ---------------------------------------------------------------------------
# Task 12: Pack card generation tests
# ---------------------------------------------------------------------------


class TestGenerateCardPacks:
    """Tests for generate_card_packs."""

    def test_returns_correct_number_of_packs(self, sample_cards):
        categorized = categorize_cards(sample_cards)
        packs = generate_card_packs(
            categorized=categorized, num_packs=3, pack_size=15, unseeded=False
        )
        assert len(packs) == 3

    def test_each_pack_has_correct_size(self, sample_cards):
        categorized = categorize_cards(sample_cards)
        packs = generate_card_packs(
            categorized=categorized, num_packs=3, pack_size=15, unseeded=False
        )
        for pack in packs:
            assert len(pack) == 15

    def test_no_duplicate_cards_across_packs(self, sample_cards):
        categorized = categorize_cards(sample_cards)
        packs = generate_card_packs(
            categorized=categorized, num_packs=2, pack_size=15, unseeded=False
        )
        all_names = []
        for pack in packs:
            all_names.extend(c.name for c in pack)
        assert len(all_names) == len(set(all_names))

    def test_packs_contain_card_objects(self, sample_cards):
        categorized = categorize_cards(sample_cards)
        packs = generate_card_packs(
            categorized=categorized, num_packs=1, pack_size=15, unseeded=False
        )
        for card in packs[0]:
            assert isinstance(card, Card)

    def test_9_card_packs(self, sample_cards):
        categorized = categorize_cards(sample_cards)
        packs = generate_card_packs(
            categorized=categorized, num_packs=2, pack_size=9, unseeded=False
        )
        for pack in packs:
            assert len(pack) == 9

    def test_insufficient_cards_raises(self, sample_cards):
        categorized = categorize_cards(sample_cards)
        with pytest.raises(ValueError, match="Not enough"):
            generate_card_packs(
                categorized=categorized, num_packs=100, pack_size=15, unseeded=False
            )


# ---------------------------------------------------------------------------
# Task 13: CLI tests
# ---------------------------------------------------------------------------


def _write_sample_cube_csv(path: Path, num_per_color: int = 20) -> None:
    """Write a sample cube CSV with enough cards for pack generation."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "quantity",
                "card name",
                "color",
                "cmc",
                "scryfall ID",
                "types",
                "card text",
            ]
        )
        colors = ["White", "Blue", "Black", "Red", "Green"]
        idx = 0
        for color in colors:
            for i in range(1, num_per_color + 1):
                idx += 1
                writer.writerow(
                    [1, f"{color} Card {i}", color, 2, f"id-{idx:04d}", "Creature", ""]
                )
        # multicolor
        for i in range(1, num_per_color + 1):
            idx += 1
            writer.writerow(
                [1, f"Gold Card {i}", "White,Blue", 3, f"id-{idx:04d}", "Creature", ""]
            )
        # lands
        for i in range(1, num_per_color + 1):
            idx += 1
            writer.writerow([1, f"Land {i}", "", 0, f"id-{idx:04d}", "Land", ""])
        # fixing
        for i in range(1, 11):
            idx += 1
            writer.writerow(
                [
                    1,
                    f"Mana Rock {i}",
                    "",
                    1,
                    f"id-{idx:04d}",
                    "Artifact",
                    "Add one mana of any color.",
                ]
            )
        # colorless
        for i in range(1, 11):
            idx += 1
            writer.writerow(
                [
                    1,
                    f"Equipment {i}",
                    "",
                    2,
                    f"id-{idx:04d}",
                    "Artifact",
                    "Equipped creature gets +1/+1.",
                ]
            )


class TestPacksCLI:
    """Tests for the packs CLI command."""

    def test_template_mode_default(self, tmp_path):
        csv_path = tmp_path / "cube.csv"
        _write_sample_cube_csv(csv_path)
        runner = CliRunner()
        # Use fewer players/packs to fit within 160-card CSV
        result = runner.invoke(
            main, ["packs", "--cube", str(csv_path), "--players", "2", "--packs", "2"]
        )
        assert result.exit_code == 0
        assert "Player 1" in result.output
        assert "Player 2" in result.output

    def test_template_mode_shows_categories(self, tmp_path):
        csv_path = tmp_path / "cube.csv"
        _write_sample_cube_csv(csv_path)
        runner = CliRunner()
        result = runner.invoke(
            main, ["packs", "--cube", str(csv_path), "--players", "2", "--packs", "1"]
        )
        assert result.exit_code == 0
        # Should contain color abbreviations
        assert "W" in result.output
        assert "multi" in result.output
        assert "land" in result.output
        assert "fixing" in result.output

    def test_cards_mode(self, tmp_path):
        csv_path = tmp_path / "cube.csv"
        _write_sample_cube_csv(csv_path)
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "packs",
                "--cube",
                str(csv_path),
                "--cards",
                "--players",
                "2",
                "--packs",
                "1",
            ],
        )
        assert result.exit_code == 0
        assert "Player 1" in result.output
        assert "Player 2" in result.output

    def test_custom_players_and_packs(self, tmp_path):
        csv_path = tmp_path / "cube.csv"
        _write_sample_cube_csv(csv_path)
        runner = CliRunner()
        result = runner.invoke(
            main, ["packs", "--cube", str(csv_path), "--players", "4", "--packs", "2"]
        )
        assert result.exit_code == 0
        assert "Player 4" in result.output
        # Should not have Player 5
        assert "Player 5" not in result.output

    def test_pack_size_option(self, tmp_path):
        csv_path = tmp_path / "cube.csv"
        _write_sample_cube_csv(csv_path)
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "packs",
                "--cube",
                str(csv_path),
                "--pack-size",
                "9",
                "--players",
                "2",
                "--packs",
                "1",
            ],
        )
        assert result.exit_code == 0

    def test_invalid_pack_size(self, tmp_path):
        csv_path = tmp_path / "cube.csv"
        _write_sample_cube_csv(csv_path)
        runner = CliRunner()
        result = runner.invoke(
            main, ["packs", "--cube", str(csv_path), "--pack-size", "12"]
        )
        assert result.exit_code != 0

    def test_cube_too_small(self, tmp_path):
        csv_path = tmp_path / "cube.csv"
        _write_sample_cube_csv(csv_path, num_per_color=2)
        runner = CliRunner()
        result = runner.invoke(
            main, ["packs", "--cube", str(csv_path), "--players", "8", "--packs", "3"]
        )
        assert result.exit_code != 0

    def test_output_dir(self, tmp_path):
        csv_path = tmp_path / "cube.csv"
        _write_sample_cube_csv(csv_path)
        output_dir = tmp_path / "output"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "packs",
                "--cube",
                str(csv_path),
                "--players",
                "2",
                "--packs",
                "1",
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0
        assert output_dir.exists()
        # Should have one file per player
        files = list(output_dir.iterdir())
        assert len(files) == 2

    def test_output_dir_cards_mode(self, tmp_path):
        csv_path = tmp_path / "cube.csv"
        _write_sample_cube_csv(csv_path)
        output_dir = tmp_path / "output"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "packs",
                "--cube",
                str(csv_path),
                "--cards",
                "--players",
                "2",
                "--packs",
                "1",
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0
        files = list(output_dir.iterdir())
        assert len(files) == 2
        # Files should contain card names
        content = files[0].read_text()
        assert "Card" in content or "Gold" in content or "Land" in content


# ---------------------------------------------------------------------------
# packs_to_templates helper
# ---------------------------------------------------------------------------


class TestPacksToTemplates:
    """Tests for packs_to_templates helper."""

    def test_converts_packs_to_templates(self, sample_cards):
        categorized = categorize_cards(sample_cards)
        packs = generate_card_packs(
            categorized=categorized, num_packs=2, pack_size=9, unseeded=True
        )
        templates = packs_to_templates(packs)
        assert len(templates) == 2
        for t in templates:
            assert t.total() == 9


# ---------------------------------------------------------------------------
# Grid Draft Templates
# ---------------------------------------------------------------------------


class TestGenerateGridTemplates:
    """Tests for generate_grid_templates."""

    def test_2_players_returns_one_pool(self, sample_cards):
        categorized = categorize_cards(sample_cards)
        pools = generate_grid_templates(players=2, categorized=categorized, num_grids=4)
        assert len(pools) == 1

    def test_3_players_returns_one_pool(self, sample_cards):
        categorized = categorize_cards(sample_cards)
        pools = generate_grid_templates(players=3, categorized=categorized, num_grids=3)
        assert len(pools) == 1

    def test_4_players_returns_two_pools(self, sample_cards):
        categorized = categorize_cards(sample_cards)
        pools = generate_grid_templates(players=4, categorized=categorized, num_grids=2)
        assert len(pools) == 2

    def test_pool_total_equals_grids_times_9(self, sample_cards):
        categorized = categorize_cards(sample_cards)
        pools = generate_grid_templates(players=2, categorized=categorized, num_grids=4)
        assert pools[0].total() == 4 * 9

    def test_3_player_pool_total_equals_grids_times_12(self, sample_cards):
        categorized = categorize_cards(sample_cards)
        pools = generate_grid_templates(players=3, categorized=categorized, num_grids=3)
        assert pools[0].total() == 3 * 12

    def test_custom_grid_count(self, sample_cards):
        categorized = categorize_cards(sample_cards)
        pools = generate_grid_templates(players=2, categorized=categorized, num_grids=3)
        assert pools[0].total() == 3 * 9

    def test_4_players_pools_are_independent(self, sample_cards):
        """Two pools for 4 players should each have the right total."""
        categorized = categorize_cards(sample_cards)
        pools = generate_grid_templates(players=4, categorized=categorized, num_grids=2)
        assert pools[0].total() == 2 * 9
        assert pools[1].total() == 2 * 9

    def test_invalid_player_count(self, sample_cards):
        categorized = categorize_cards(sample_cards)
        with pytest.raises(ValueError, match="2, 3, or 4"):
            generate_grid_templates(players=5, categorized=categorized)


class TestGridCLI:
    """Tests for the --grid CLI flag."""

    @pytest.fixture
    def csv_path(self, tmp_path):
        """Create a CSV with enough cards for grid draft."""
        p = tmp_path / "cube.csv"
        rows = [
            [
                "quantity",
                "card name",
                "color",
                "cmc",
                "scryfall ID",
                "types",
                "card text",
            ]
        ]
        idx = 0
        for color in ["White", "Blue", "Black", "Red", "Green"]:
            for i in range(40):
                rows.append(
                    [1, f"{color} Card {i}", color, 2, f"id-{idx}", "Creature", ""]
                )
                idx += 1
        for i in range(30):
            rows.append(
                [1, f"Gold {i}", "White,Blue", 3, f"id-{idx}", "Creature", "multi"]
            )
            idx += 1
        for i in range(30):
            rows.append([1, f"Land {i}", "", 0, f"id-{idx}", "Land", ""])
            idx += 1
        for i in range(15):
            rows.append(
                [
                    1,
                    f"Fixer {i}",
                    "",
                    1,
                    f"id-{idx}",
                    "Artifact",
                    "add one mana of any color",
                ]
            )
            idx += 1
        for i in range(15):
            rows.append([1, f"Artifact {i}", "", 2, f"id-{idx}", "Artifact", "vanilla"])
            idx += 1
        with p.open("w", newline="") as f:
            csv.writer(f).writerows(rows)
        return p

    def test_grid_2_players(self, csv_path):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "packs",
                "--cube",
                str(csv_path),
                "--grid",
                "--players",
                "2",
                "--grids",
                "10",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Grid draft: 2 players" in result.output
        assert "Draw pile:" in result.output

    def test_grid_4_players(self, csv_path):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "packs",
                "--cube",
                str(csv_path),
                "--grid",
                "--players",
                "4",
                "--grids",
                "5",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Pool 1:" in result.output
        assert "Pool 2:" in result.output

    def test_grid_custom_grids(self, csv_path):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "packs",
                "--cube",
                str(csv_path),
                "--grid",
                "--players",
                "2",
                "--grids",
                "8",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "8 grids" in result.output

    def test_grid_invalid_players(self, csv_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["packs", "--cube", str(csv_path), "--grid", "--players", "5"]
        )
        assert result.exit_code != 0
