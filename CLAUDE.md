# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync                          # Install dependencies
uv run pytest                    # Run all tests
uv run pytest tests/test_packs.py::TestGenerateCardPacks::test_9_card_packs  # Run a single test
uv run cube-utils packs --cube regular-cube.csv --players 8   # Run CLI
```

Git commits in this repo use `--no-gpg-sign`.

## Architecture

MTG cube draft utilities: a Click CLI (`cube-utils`) with three commands (`packs`, `guide`, `fetch-tags`) backed by four modules.

### Data flow

```
CSV → load_cube → Card objects → categorize_cards → dict[Category, list[Card]]
                       ↓ (optional)                          ↓
              enrich_with_scryfall          ┌─────────────────┼──────────────┐
              enrich_with_tags             packs            guide          CLI output
```

### Modules

- **`cards.py`** — `Card` dataclass (10 fields), CSV loading (`load_cube`), 9-category classification (`categorize_cards`), Scryfall enrichment. Enrichment mutates cards in place; categorization returns a new dict. Each card belongs to exactly one category.

- **`packs.py`** — Pack generation with two modes:
  - **Seeded** (default): `PackStructure` defines slot ranges per pack size (9/11/15). `generate_pack_templates` randomizes within those ranges (complementary multi/land slots, random extra mono distribution). `generate_card_packs` draws from shuffled category pools to fill templates.
  - **Unseeded** (`unseeded=True`): Shuffles all cards together, batches with `itertools.batched`.
  - **Grid draft**: `generate_grid_templates` produces pool-level category counts. Uses unseeded card packs internally. 3-player grids use 12-card packs (refill mechanic); 4-player = two parallel 2-player drafts.

- **`guide.py`** — Theme detection via three layers: Scryfall oracle tags (primary), Scryfall keywords, card text patterns (fallback). 15 themes defined in `Theme` enum with patterns in `THEME_PATTERNS`. `analyze_color_pairs` finds shared themes across 10 two-color pairs. `find_bridge_cards` identifies cards in 2+ themes.

- **`tags.py`** — Fetches oracle tags from Scryfall API (`otag:` search), paginates results, caches to JSON. 100ms rate limiting between requests. 12 relevant tags defined in `RELEVANT_TAGS`.

### Categories (mutually exclusive)

MONO_WHITE, MONO_BLUE, MONO_BLACK, MONO_RED, MONO_GREEN, MULTICOLOR, LAND, FIXING, COLORLESS. Fixing is detected via regex patterns for mana-producing lands/artifacts (defined in `_FIXING_PATTERNS`).

## Testing

Tests use Click's `CliRunner` for CLI tests, `unittest.mock` for Scryfall API calls, and fixtures in `conftest.py` that create minimal test data (7-card CSV, ~290-card sample set). Grid draft tests use reduced grid counts to fit within fixture card pools.
