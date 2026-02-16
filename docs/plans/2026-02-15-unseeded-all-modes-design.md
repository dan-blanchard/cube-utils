# Unseeded Packs for All Modes

## Problem

The `--unseeded` flag on `cube-utils packs` only works in `--cards` mode. In the default template mode, it is silently ignored, always producing seeded templates with fixed category slots (1 fixing, 2-3 multi/land).

## Approach

Generate-then-categorize, matching the existing grid mode pattern.

### `packs.py`

Extract `_packs_to_templates(packs: list[list[Card]]) -> list[PackTemplate]` from the categorize-and-count logic in `generate_grid_templates`. Takes a list of card packs, categorizes each, and returns `PackTemplate`s with per-category counts. `generate_grid_templates` calls this helper instead of inlining the logic.

### `cli.py`

Template mode (`else` branch, no `--cards`): when `unseeded=True`, call `generate_card_packs(unseeded=True)` then `_packs_to_templates()` to produce templates with proportional counts. Display them identically to seeded templates.

Move the `get_pack_structure()` validation behind `if not unseeded` so unseeded mode accepts arbitrary pack sizes.

### Tests

- Unseeded template mode produces packs whose category counts sum to `pack_size`.
- Unseeded works with a non-standard pack size (e.g., 13).
- Unseeded template mode produces varying category distributions across packs.
