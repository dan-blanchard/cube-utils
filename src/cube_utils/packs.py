"""Pack generation for cube drafting."""

import random
from dataclasses import dataclass

from cube_utils.cards import Card, Category


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
        raise ValueError(
            f"Unsupported pack size: {pack_size}. Must be one of {sorted(_PACK_STRUCTURES)}"
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


def generate_pack_templates(num_packs: int, pack_size: int) -> list[PackTemplate]:
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
        land_count = (
            structure.land_range[1]
            - (multi_count - structure.multicolor_range[0])
        )

        # Start with 1 per color
        color_counts = {c: 1 for c in _COLOR_ATTRS}

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


_CATEGORY_FOR_COLOR = {
    "white": Category.MONO_WHITE,
    "blue": Category.MONO_BLUE,
    "black": Category.MONO_BLACK,
    "red": Category.MONO_RED,
    "green": Category.MONO_GREEN,
}


def generate_card_packs(
    categorized: dict[Category, list[Card]],
    num_packs: int,
    pack_size: int,
) -> list[list[Card]]:
    """Generate draft packs filled with actual cards.

    Args:
        categorized: Dict mapping Category to list of Card (from categorize_cards).
        num_packs: Number of packs to generate.
        pack_size: Cards per pack (9, 11, or 15).

    Returns:
        List of packs, where each pack is a list of Card.

    Raises:
        ValueError: If there are not enough cards to fill all packs.
    """
    # Copy and shuffle pools so we don't modify the original
    pools: dict[Category, list[Card]] = {}
    for cat, cards in categorized.items():
        pool = list(cards)
        random.shuffle(pool)
        pools[cat] = pool

    templates = generate_pack_templates(num_packs, pack_size)

    # Check we have enough cards in each category across all templates
    needed: dict[Category, int] = {cat: 0 for cat in Category}
    for t in templates:
        for color_attr in _COLOR_ATTRS:
            needed[_CATEGORY_FOR_COLOR[color_attr]] += getattr(t, color_attr)
        needed[Category.COLORLESS] += t.colorless
        needed[Category.MULTICOLOR] += t.multicolor
        needed[Category.LAND] += t.land
        needed[Category.FIXING] += t.fixing

    for cat, count in needed.items():
        available = len(pools.get(cat, []))
        if count > available:
            raise ValueError(
                f"Not enough {cat.value} cards: need {count}, have {available}"
            )

    # Draw cards into packs
    packs: list[list[Card]] = []
    for template in templates:
        pack: list[Card] = []

        # Draw mono-colored cards
        for color_attr in _COLOR_ATTRS:
            cat = _CATEGORY_FOR_COLOR[color_attr]
            count = getattr(template, color_attr)
            for _ in range(count):
                pack.append(pools[cat].pop())

        # Draw colorless
        for _ in range(template.colorless):
            pack.append(pools[Category.COLORLESS].pop())

        # Draw multicolor
        for _ in range(template.multicolor):
            pack.append(pools[Category.MULTICOLOR].pop())

        # Draw land
        for _ in range(template.land):
            pack.append(pools[Category.LAND].pop())

        # Draw fixing
        for _ in range(template.fixing):
            pack.append(pools[Category.FIXING].pop())

        packs.append(pack)

    return packs
