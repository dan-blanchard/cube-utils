import click

from pathlib import Path

from cube_utils.cards import (
    Category,
    categorize_cards,
    enrich_with_scryfall,
    enrich_with_tags,
    load_cube,
)
from cube_utils.guide import (
    analyze_color_pairs,
    detect_themes,
    find_bridge_cards,
    generate_guide_markdown,
)
from cube_utils.packs import (
    generate_card_packs,
    generate_pack_templates,
    get_pack_structure,
)
from cube_utils.tags import fetch_tags


_COLOR_SHORT = {
    "white": "W",
    "blue": "U",
    "black": "B",
    "red": "R",
    "green": "G",
}

_CATEGORY_LABEL = {
    Category.MONO_WHITE: "White",
    Category.MONO_BLUE: "Blue",
    Category.MONO_BLACK: "Black",
    Category.MONO_RED: "Red",
    Category.MONO_GREEN: "Green",
    Category.MULTICOLOR: "Multicolor",
    Category.LAND: "Land",
    Category.FIXING: "Fixing",
    Category.COLORLESS: "Colorless",
}


def _format_template(template) -> str:
    """Format a PackTemplate as a compact string like '2W 1U 1B 2R 1G 1colorless 3multi 2land 1fixing'."""
    parts = []
    for attr, short in _COLOR_SHORT.items():
        count = getattr(template, attr)
        parts.append(f"{count}{short}")
    parts.append(f"{template.colorless}colorless")
    parts.append(f"{template.multicolor}multi")
    parts.append(f"{template.land}land")
    parts.append(f"{template.fixing}fixing")
    return " ".join(parts)


def _format_pack_cards(pack, categorized) -> str:
    """Format a list of cards grouped by category."""
    # Build reverse lookup: card name -> category
    card_to_cat = {}
    for cat, cards in categorized.items():
        for card in cards:
            card_to_cat[card.name] = cat

    # Group pack cards by category
    groups: dict[Category, list[str]] = {cat: [] for cat in Category}
    for card in pack:
        cat = card_to_cat.get(card.name, Category.COLORLESS)
        groups[cat].append(card.name)

    lines = []
    for cat in Category:
        names = groups[cat]
        if names:
            label = _CATEGORY_LABEL[cat]
            lines.append(f"  {label}: {', '.join(sorted(names))}")
    return "\n".join(lines)


@click.group()
def main():
    """MTG cube draft utilities."""


@main.command()
@click.option(
    "--cube",
    "cube_path",
    default="cube-2.csv",
    type=click.Path(exists=True),
    help="Path to the cube CSV file.",
)
@click.option(
    "--players",
    default=8,
    type=int,
    help="Number of players.",
)
@click.option(
    "--packs",
    "num_packs",
    default=3,
    type=int,
    help="Number of packs per player.",
)
@click.option(
    "--pack-size",
    default=15,
    type=int,
    help="Cards per pack (9, 11, or 15).",
)
@click.option(
    "--cards",
    "cards_mode",
    is_flag=True,
    default=False,
    help="Show actual card names instead of category counts.",
)
@click.option(
    "--output-dir",
    "output_dir",
    default=None,
    type=click.Path(),
    help="Write one file per player to this directory.",
)
def packs(cube_path, players, num_packs, pack_size, cards_mode, output_dir):
    """Generate draft packs."""
    # Validate pack size
    try:
        get_pack_structure(pack_size)
    except ValueError as e:
        raise click.ClickException(str(e))

    cards = load_cube(Path(cube_path))
    categorized = categorize_cards(cards)

    total_packs = players * num_packs
    total_cards_needed = total_packs * pack_size

    if total_cards_needed > len(cards):
        raise click.ClickException(
            f"Not enough cards: need {total_cards_needed} but cube has {len(cards)}"
        )

    if cards_mode:
        try:
            all_packs = generate_card_packs(categorized, total_packs, pack_size)
        except ValueError as e:
            raise click.ClickException(str(e))

        output_parts = []
        for player_idx in range(players):
            player_lines = [f"Player {player_idx + 1}"]
            for pack_idx in range(num_packs):
                pack = all_packs[player_idx * num_packs + pack_idx]
                player_lines.append(f"  Pack {pack_idx + 1}:")
                player_lines.append(_format_pack_cards(pack, categorized))
            output_parts.append("\n".join(player_lines))

        output_text = "\n\n".join(output_parts) + "\n"
    else:
        templates = generate_pack_templates(total_packs, pack_size)

        output_parts = []
        for player_idx in range(players):
            player_lines = [f"Player {player_idx + 1}"]
            for pack_idx in range(num_packs):
                template = templates[player_idx * num_packs + pack_idx]
                player_lines.append(
                    f"  Pack {pack_idx + 1}: {_format_template(template)}"
                )
            output_parts.append("\n".join(player_lines))

        output_text = "\n\n".join(output_parts) + "\n"

    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        for player_idx in range(players):
            player_file = out_path / f"player-{player_idx + 1}.txt"
            # Extract just this player's section
            player_file.write_text(
                output_parts[player_idx] + "\n", encoding="utf-8"
            )
        click.echo(f"Wrote {players} player files to {output_dir}")
    else:
        click.echo(output_text, nl=False)


@main.command("fetch-tags")
@click.option(
    "--output",
    "output_path",
    default="scryfall-tags-cache.json",
    type=click.Path(),
    help="Path to write the tags cache file.",
)
def fetch_tags_cmd(output_path):
    """Fetch Scryfall oracle tags and cache locally."""
    click.echo(f"Fetching oracle tags from Scryfall...")
    cache = fetch_tags(cache_path=Path(output_path))
    tag_counts = {tag: len(ids) for tag, ids in cache["tags"].items()}
    total = sum(tag_counts.values())
    click.echo(f"Cached {len(tag_counts)} tags ({total} total oracle IDs) to {output_path}")
    for tag, count in sorted(tag_counts.items()):
        click.echo(f"  {tag}: {count} cards")


@main.command()
@click.option(
    "--cube",
    "cube_path",
    default="cube-2.csv",
    type=click.Path(exists=True),
)
@click.option(
    "--scryfall",
    "scryfall_path",
    default=None,
    type=click.Path(exists=True),
)
@click.option(
    "--tags-cache",
    "tags_cache_path",
    default=None,
    type=click.Path(exists=True),
    help="Path to Scryfall oracle tags cache file.",
)
@click.option(
    "--output",
    "output_path",
    default=None,
    type=click.Path(),
)
def guide(cube_path, scryfall_path, tags_cache_path, output_path):
    """Generate draft guide skeleton."""
    cards = load_cube(Path(cube_path))

    if scryfall_path:
        enrich_with_scryfall(cards, Path(scryfall_path))

    if tags_cache_path:
        enrich_with_tags(cards, Path(tags_cache_path))

    themes = detect_themes(cards)
    pairs = analyze_color_pairs(cards, themes)
    bridges = find_bridge_cards(themes)
    markdown = generate_guide_markdown(themes, pairs, bridges)

    if output_path:
        Path(output_path).write_text(markdown, encoding="utf-8")
        click.echo(f"Guide written to {output_path}")
    else:
        click.echo(markdown)
