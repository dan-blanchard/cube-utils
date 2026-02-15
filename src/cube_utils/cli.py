import click

from pathlib import Path

from cube_utils.cards import load_cube, enrich_with_scryfall
from cube_utils.guide import (
    analyze_color_pairs,
    detect_themes,
    find_bridge_cards,
    generate_guide_markdown,
)


@click.group()
def main():
    """MTG cube draft utilities."""


@main.command()
def packs():
    """Generate draft packs."""
    click.echo("packs command (not yet implemented)")


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
    "--output",
    "output_path",
    default=None,
    type=click.Path(),
)
def guide(cube_path, scryfall_path, output_path):
    """Generate draft guide skeleton."""
    cards = load_cube(Path(cube_path))

    if scryfall_path:
        enrich_with_scryfall(cards, Path(scryfall_path))

    themes = detect_themes(cards)
    pairs = analyze_color_pairs(cards, themes)
    bridges = find_bridge_cards(themes)
    markdown = generate_guide_markdown(themes, pairs, bridges)

    if output_path:
        Path(output_path).write_text(markdown, encoding="utf-8")
        click.echo(f"Guide written to {output_path}")
    else:
        click.echo(markdown)
