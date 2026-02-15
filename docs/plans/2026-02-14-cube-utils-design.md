# cube_utils Design

## Overview

A Python CLI tool for managing an MTG cube draft experience. Two main commands:
- `cube-utils packs` — generate seeded draft packs
- `cube-utils guide` — analyze card data to produce a draft guide skeleton

The cube is a ~465-card modified Regular Cube: synergy-focused, lower power level, creature-centric, with overlapping themes across colors.

## Project Structure

```
cube_utils/
├── pyproject.toml
├── cube-2.csv                  # Cube card list
├── default-cards-*.json        # Scryfall bulk data
├── docs/
│   ├── plans/
│   │   └── 2026-02-14-cube-utils-design.md
│   └── draft-guide.md          # Final hand-written guide
├── src/
│   └── cube_utils/
│       ├── __init__.py
│       ├── cli.py              # Click-based CLI
│       ├── cards.py            # Card loading, categorization, Scryfall enrichment
│       ├── packs.py            # Pack generation logic
│       └── guide.py            # Draft guide generation/analysis
└── tests/
    ├── test_cards.py
    ├── test_packs.py
    └── test_guide.py
```

## Card Categorization

Each card from the cube CSV is assigned to exactly one category:

| Category | Rule | ~Count |
|----------|------|--------|
| `mono_white` | color == "White" | 66 |
| `mono_blue` | color == "Blue" | 64 |
| `mono_black` | color == "Black" | 62 |
| `mono_green` | color == "Green" | 62 |
| `mono_red` | color == "Red" | 59 |
| `multicolor` | 2+ colors | 63 |
| `land` | colorless + "Land" in types | 53 |
| `fixing` | colorless artifact that produces/fetches mana | ~8-10 |
| `colorless` | remaining colorless non-land, non-fixing | ~18-20 |

Tokens and non-draftable entries (e.g., "On an Adventure") are excluded from the draft pool.

Scryfall bulk data is used to enrich cards with additional metadata (keywords, color identity) for guide generation.

## Pack Generation

### Pack Structure (15-card packs)

| Slot | Count | Pool |
|------|-------|------|
| 1 per color | 5 | one from each mono pool |
| Colorless | 1 | colorless |
| Multicolor | 2-3 | multicolor |
| Lands | 2-3 | land |
| Fixing | 1 | fixing |
| Random mono | 2-4 | random color from mono pools |

Multicolor/land split randomizes between 2+3 or 3+2 per pack, keeping total at 5. Random mono slots pick specific colors, which are folded into the per-color totals.

### Scaling for Smaller Packs

| Format | Pack Size | Structure |
|--------|-----------|-----------|
| 3x15 (8 players) | 15 | 5 mono + 1 colorless + 2-3 multi + 2-3 land + 1 fixing + 2-4 mono |
| 4x11 (4 players) | 11 | 5 mono + 1 colorless + 1-2 multi + 1-2 land + 1 fixing + 0-1 mono |
| 5x9 (4 players) | 9 | 5 mono + 1 fixing + 1 multi + 1 land + 1 colorless |
| Grid draft (2 players) | 9 | Same as 5x9 |

Principle: always guarantee 1 of each mono color and 1 fixing. Flex slots scale down.

### Output Modes

**Template mode (default):** Shows count breakdown per category for each pack. Random mono slots are folded into per-color totals.

```
Pack 1:  2W  2U  1B  1R  1G  1colorless  3multi  2land  1fixing
Pack 2:  1W  1U  2B  1R  2G  1colorless  2multi  3land  1fixing
Pack 3:  1W  2U  1B  2R  1G  1colorless  2multi  2land  1fixing
```

**Cards mode (`--cards`):** Lists actual card names per pack.

### CLI

```
cube-utils packs                              # template mode, 8 players, 3x15
cube-utils packs --cards                      # card names mode
cube-utils packs --players 4 --packs 4 --pack-size 11
cube-utils packs --players 2 --packs 1 --pack-size 9 --grid
cube-utils packs --output-dir ./draft-packs/  # write to files
cube-utils packs --cube path/to/cube.csv      # custom cube file
```

Validates that the cube has enough cards for the requested format before generating.

## Draft Guide

### Guide Generator Tool

`cube-utils guide` analyzes card data to produce a skeleton:

- **Detect themes** by scanning card text for keyword clusters (sacrifice, +1/+1 counters, ETB, prowess/noncreature, etc.)
- **Map themes to colors** — which colors support each theme most
- **Identify bridge cards** — cards touching multiple themes
- **Color pair summary** — multicolor cards and overlapping themes per 2-color pair

```
cube-utils guide                                    # print to terminal
cube-utils guide --output draft-guide-skeleton.md   # write to file
cube-utils guide --cube path/to/cube.csv
```

### Hand-Written Guide

A polished markdown document (`docs/draft-guide.md`) built from the generator output, covering:

- Overview of the environment
- General drafting tips
- Color pair archetypes (all 10 pairs)
- Key cross-color themes and how they overlap
- Traps to avoid

## Implementation Order

1. Card loading/categorization (`cards.py`)
2. Guide generator (`guide.py` + CLI)
3. Run guide generator, review output, iterate
4. Write final draft guide using generator output as skeleton
5. Pack generator (`packs.py` + CLI)
