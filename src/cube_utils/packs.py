"""Pack generation for cube drafting."""

import itertools
import random
from dataclasses import dataclass

from cube_utils.cards import Card, Category, categorize_cards


@dataclass
class PackStructure:
    """Defines the slot distribution for a draft pack."""

    mono_per_color: int
    colorless: int
    multicolor_range: tuple[int, int]
    land_range: tuple[int, int]
    fixing: int
    extra_mono: int

    def total(self) -> int:
        """Calculate the total pack size.

        Uses the midpoint of multi/land ranges since they are complementary
        (when multi is max, land is min and vice versa).
        """
        base_mono = self.mono_per_color * 5
        # multi and land ranges are complementary, so use min of each
        # which together equal the consistent total
        multi_land = self.multicolor_range[0] + self.land_range[1]
        return base_mono + self.colorless + multi_land + self.fixing + self.extra_mono


_PACK_STRUCTURES = {
    15: PackStructure(
        mono_per_color=1,
        colorless=1,
        multicolor_range=(2, 3),
        land_range=(2, 3),
        fixing=1,
        extra_mono=3,
    ),
    11: PackStructure(
        mono_per_color=1,
        colorless=1,
        multicolor_range=(1, 2),
        land_range=(1, 2),
        fixing=1,
        extra_mono=1,
    ),
    9: PackStructure(
        mono_per_color=1,
        colorless=1,
        multicolor_range=(1, 1),
        land_range=(1, 1),
        fixing=1,
        extra_mono=0,
    ),
}


def get_pack_structure(pack_size: int) -> PackStructure:
    """Return the PackStructure for a given pack size.

    Args:
        pack_size: The number of cards per pack (9, 11, or 15).

    Returns:
        The corresponding PackStructure.

    Raises:
        ValueError: If pack_size is not a supported size.
    """
    if pack_size not in _PACK_STRUCTURES:
        supported = sorted(_PACK_STRUCTURES)
        raise ValueError(
            f"Unsupported pack size: {pack_size}. Must be one of {supported}"
        )
    return _PACK_STRUCTURES[pack_size]


@dataclass
class PackTemplate:
    """Concrete slot counts for a single pack."""

    white: int
    blue: int
    black: int
    red: int
    green: int
    colorless: int
    multicolor: int
    land: int
    fixing: int

    def total(self) -> int:
        """Return the total number of card slots."""
        return (
            self.white
            + self.blue
            + self.black
            + self.red
            + self.green
            + self.colorless
            + self.multicolor
            + self.land
            + self.fixing
        )


_COLOR_ATTRS = ["white", "blue", "black", "red", "green"]


def generate_pack_templates(*, num_packs: int, pack_size: int) -> list[PackTemplate]:
    """Generate randomized pack templates for a draft.

    Args:
        num_packs: Number of packs to generate.
        pack_size: Cards per pack (9, 11, or 15).

    Returns:
        List of PackTemplate with randomized slot distributions.
    """
    structure = get_pack_structure(pack_size)
    templates: list[PackTemplate] = []

    for _ in range(num_packs):
        # Randomize the multi/land split within their complementary ranges
        multi_count = random.randint(
            structure.multicolor_range[0], structure.multicolor_range[1]
        )
        # Land is complementary: when multi is high, land is low
        land_count = structure.land_range[1] - (
            multi_count - structure.multicolor_range[0]
        )

        # Start with 1 per color
        color_counts = dict.fromkeys(_COLOR_ATTRS, 1)

        # Distribute extra_mono slots to random colors
        for _ in range(structure.extra_mono):
            color = random.choice(_COLOR_ATTRS)
            color_counts[color] += 1

        templates.append(
            PackTemplate(
                white=color_counts["white"],
                blue=color_counts["blue"],
                black=color_counts["black"],
                red=color_counts["red"],
                green=color_counts["green"],
                colorless=structure.colorless,
                multicolor=multi_count,
                land=land_count,
                fixing=structure.fixing,
            )
        )

    return templates


_DEFAULT_GRIDS = 18


def generate_grid_templates(
    *,
    players: int,
    categorized: dict[Category, list[Card]],
    num_grids: int = _DEFAULT_GRIDS,
) -> list[PackTemplate]:
    """Generate pool templates for grid drafting.

    Grid drafts use a shared draw pile instead of individual packs. Each grid
    is 9 cards laid out in a 3x3 arrangement. This function generates one
    combined template per pool, with category counts summed from individual
    9-card pack templates.

    Note: For 3-player grids, the first player picks from a 9x9 grid,
          and then the grid refills to 9 cards for the next player,
          so we generate 12-card templates to account for the extra cards
          needed.

    Args:
        players: Number of players (2, 3, or 4).
        num_grids: Number of 9-card grids per pool (default 18).

    Returns:
        List of PackTemplate, one per pool. 2 or 3 players get 1 pool,
        4 players get 2 pools (parallel grid drafts).

    Raises:
        ValueError: If players is not 2, 3, or 4.
    """
    if players not in (2, 3, 4):
        raise ValueError(f"Grid draft supports 2, 3, or 4 players, not {players}")

    num_pools = 2 if players == 4 else 1
    pool_templates: list[PackTemplate] = []

    grid_size = (
        9 if players != 3 else 12
    )  # 3-player grids refill after first player picks
    packs = generate_card_packs(
        categorized=categorized,
        num_packs=num_grids * num_pools,
        pack_size=grid_size,
        unseeded=True,
    )

    for i in range(num_pools):
        # Convert packs to templates and sum them into one pool template
        packs_for_pool = packs[i * num_grids : (i + 1) * num_grids]

        pool = PackTemplate(**dict.fromkeys(_ATTR_TO_CATEGORY, 0))
        for pack in packs_for_pool:
            categorized_pack = categorize_cards(pack)
            for attr, cat in _ATTR_TO_CATEGORY.items():
                setattr(pool, attr, getattr(pool, attr) + len(categorized_pack[cat]))
        pool_templates.append(pool)

    return pool_templates


_CATEGORY_FOR_COLOR = {
    "white": Category.MONO_WHITE,
    "blue": Category.MONO_BLUE,
    "black": Category.MONO_BLACK,
    "red": Category.MONO_RED,
    "green": Category.MONO_GREEN,
}

# Maps PackTemplate attribute names to their Category, used for drawing cards
# and accumulating grid template counts.
_ATTR_TO_CATEGORY = {
    **_CATEGORY_FOR_COLOR,
    "colorless": Category.COLORLESS,
    "multicolor": Category.MULTICOLOR,
    "land": Category.LAND,
    "fixing": Category.FIXING,
}


def generate_card_packs(
    *,
    categorized: dict[Category, list[Card]],
    num_packs: int,
    pack_size: int,
    unseeded: bool,
) -> list[list[Card]]:
    """Generate draft packs filled with actual cards.

    Args:
        categorized: Dict mapping Category to list of Card (from categorize_cards).
        num_packs: Number of packs to generate.
        pack_size: Cards per pack (9, 11, or 15).
        unseeded: Should packs be fully random?

    Returns:
        List of packs, where each pack is a list of Card.

    Raises:
        ValueError: If there are not enough cards to fill all packs.
    """
    packs: list[list[Card]] = []

    # Copy and shuffle pools so we don't modify the original
    pools: dict[Category, list[Card]] = {}
    for cat, cards in categorized.items():
        pool = list(cards)
        random.shuffle(pool)
        pools[cat] = pool

    if not unseeded:
        templates = generate_pack_templates(num_packs=num_packs, pack_size=pack_size)

        # Check we have enough cards in each category across all templates
        needed: dict[Category, int] = dict.fromkeys(Category, 0)
        for t in templates:
            for attr, cat in _ATTR_TO_CATEGORY.items():
                needed[cat] += getattr(t, attr)

        for cat, count in needed.items():
            available = len(pools.get(cat, []))
            if count > available:
                raise ValueError(
                    f"Not enough {cat.value} cards: need {count}, have {available}"
                )

        # Draw cards into packs
        for template in templates:
            pack: list[Card] = []
            for attr, cat in _ATTR_TO_CATEGORY.items():
                for _ in range(getattr(template, attr)):
                    pack.append(pools[cat].pop())  # noqa: PERF401
            packs.append(pack)
    else:
        full_pool = list(itertools.chain.from_iterable(pools.values()))
        random.shuffle(full_pool)
        packs = [
            list(batch)
            for batch in itertools.batched(
                full_pool[: pack_size * num_packs], pack_size, strict=True
            )
        ]

    return packs
