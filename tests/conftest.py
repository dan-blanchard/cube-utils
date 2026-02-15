"""Shared test fixtures for cube_utils tests."""

import csv
import io
import textwrap
from pathlib import Path

import pytest


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    """Create a sample cube CSV file for testing."""
    csv_path = tmp_path / "cube.csv"
    csv_path.write_text(
        textwrap.dedent("""\
            quantity,card name,color,cmc,scryfall ID,types,card text
            1,Lightning Bolt,"Red",1,e3285e6b-3e79-4d7c-bf96-d920f973b122,"Instant","Lightning Bolt deals 3 damage to any target."
            1,Counterspell,"Blue",2,1920dae4-fb92-4f19-ae4b-eb3276b8571c,"Instant","Counter target spell."
            1,Anax and Cymede,"White,Red",3,71d9fd43-576f-45db-ab8f-a9f2a0427398,"Creature","First strike, vigilance Heroic -- Whenever you cast a spell that targets Anax and Cymede, creatures you control get +1/+1 and gain trample until end of turn."
            1,Chromatic Sphere,"",1,fd71f597-ad12-4d2b-93af-3f8dfe4027b2,"Artifact","{1}, {T}, Sacrifice this artifact: Add one mana of any color. Draw a card."
            1,Evolving Wilds,"",0,31181bd2-3a1f-4cb9-ba30-637ac479133a,"Land","{T}, Sacrifice this land: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle."
            1,Access Tunnel,"",0,4bef5957-71a4-4fe0-b2ce-dff8e8690bd9,"Land","{T}: Add {C}. {3}, {T}: Target creature with power 3 or less can't be blocked this turn."
            1,Goblin,"Red",0,e265ca24-96c0-4654-a8f3-bbffe288970a,"Creature,Token","undefined // undefined"
            1,On an Adventure,"",0,fcf4c7fb-7859-4c11-8552-6817f5119d2e,"Card","After an Adventure resolves, you can place the exiled card here. You may cast the creature from exile."
            1,Mask of Memory,"",2,c6c4dffd-0ae9-493d-afa4-d1eb8bdba582,"Artifact","Whenever equipped creature deals combat damage to a player, you may draw two cards. If you do, discard a card. Equip {1}"
        """)
    )
    return csv_path


@pytest.fixture
def real_cube_path() -> Path:
    """Path to the real cube CSV file."""
    return Path(__file__).parent.parent / "cube-2.csv"
