import click

from pathlib import Path

from cube_utils.cards import enrich_with_scryfall, enrich_with_tags, load_cube
from cube_utils.guide import (
    analyze_color_pairs,
    detect_themes,
    find_bridge_cards,
    generate_guide_markdown,
)
from cube_utils.tags import fetch_tags


@click.group()
def main():
    """MTG cube draft utilities."""


@main.command()
def packs():
    """Generate draft packs."""
    click.echo("packs command (not yet implemented)")


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
