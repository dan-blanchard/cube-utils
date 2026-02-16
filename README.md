# cube-utils

CLI tools for MTG cube drafting. Generate balanced draft packs (seeded or random), grid draft pools, and draft guide skeletons enriched with [Scryfall](https://scryfall.com/) data and oracle tags.

## Installation

Requires Python 3.12+.

```bash
uv sync
```

## Usage

### Generate draft packs

```bash
# Template mode (default) — shows category counts per pack
cube-utils packs --cube regular-cube.csv --players 8

# Cards mode — shows actual card names
cube-utils packs --cube regular-cube.csv --players 4 --packs 4 --pack-size 11 --cards

# Unseeded (fully random) packs
cube-utils packs --cube regular-cube.csv --players 2 --unseeded --cards

# Write one file per player
cube-utils packs --cube regular-cube.csv --output-dir draft-packs/
```

Supported pack sizes: 9, 11, or 15 cards. Seeded packs guarantee at least one card of each color and balance multicolor, land, fixing, and colorless slots.

### Grid draft

```bash
# 2-player grid draft (one shared pool)
cube-utils packs --cube regular-cube.csv --grid --players 2

# 4-player grid draft (two parallel pools)
cube-utils packs --cube regular-cube.csv --grid --players 4

# Custom number of grids
cube-utils packs --cube regular-cube.csv --grid --players 2 --grids 12
```

Grid draft pools are fully random (unseeded). 3-player grids use 12-card grids to account for the refill mechanic.

### Generate a draft guide

```bash
# Fetch Scryfall oracle tags (cached locally)
cube-utils fetch-tags

# Generate guide skeleton with Scryfall enrichment
cube-utils guide --cube regular-cube.csv --scryfall default-cards-*.json --tags-cache scryfall-tags-cache.json --output docs/draft-guide-skeleton.md
```

The guide command detects themes and color pair synergies across your cube and outputs a markdown skeleton you can edit into a full draft guide.

## Development

```bash
uv sync
uv run pytest
```

## License

MIT
