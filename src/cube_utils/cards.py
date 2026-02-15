"""Card data model and cube CSV loading."""

import csv
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Card:
    """Represents a single MTG card in the cube."""

    name: str
    colors: list[str]
    cmc: int
    scryfall_id: str
    types: list[str]
    text: str
    keywords: list[str] = field(default_factory=list)

    @property
    def is_multicolor(self) -> bool:
        """True if the card has more than one color."""
        return len(self.colors) > 1

    @property
    def is_colorless(self) -> bool:
        """True if the card has no colors."""
        return len(self.colors) == 0

    @property
    def is_land(self) -> bool:
        """True if the card is colorless and has Land in its types."""
        return self.is_colorless and "Land" in self.types

    @property
    def is_token(self) -> bool:
        """True if the card has Token in its types."""
        return "Token" in self.types

    @property
    def is_draftable(self) -> bool:
        """True if the card is not a token and not a Card type."""
        return not self.is_token and "Card" not in self.types


def load_cube(path: Path) -> list[Card]:
    """Load cube cards from a CSV file, excluding non-draftable entries.

    Args:
        path: Path to the cube CSV file.

    Returns:
        List of draftable Card objects.
    """
    cards: list[Card] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            # CSV columns: quantity, card name, color, cmc, scryfall ID, types, card text
            # Card text may contain commas, so rejoin everything after column 6
            quantity = row[0]
            name = row[1]
            color_str = row[2]
            cmc = int(row[3])
            scryfall_id = row[4]
            types_str = row[5]
            text = ",".join(row[6:])

            colors = [c.strip() for c in color_str.split(",") if c.strip()]
            types = [t.strip() for t in types_str.split(",") if t.strip()]

            card = Card(
                name=name,
                colors=colors,
                cmc=cmc,
                scryfall_id=scryfall_id,
                types=types,
                text=text,
            )

            if card.is_draftable:
                cards.append(card)

    return cards
