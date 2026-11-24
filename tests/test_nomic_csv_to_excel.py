from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from scripts.nomic_csv_to_excel import process_rak
from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.llm.rakdeel_omschrijving import RakdeelOmschrijving
from tekstherkenning_ark.models.bovenbouw import Bovenbouw
from tekstherkenning_ark.models.gebrek import Gebrek, ScheurHout
from tekstherkenning_ark.models.onderbouw import Onderbouw
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.models.rakdeel import Rakdeel


def test_process_rak_enriches_missing_fields_and_classifies_generic_defects(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enrich empty Nomic fields without overwriting CSV data and classify generic defects."""
    rakdeel = Rakdeel(
        rakdeel_id="Constructie A",
        omschrijving="Houten onderbouw uit 1990.",
        bouwjaar=1990,
        bovenbouw=Bovenbouw(),
        onderbouw=Onderbouw(palen=[], kespen=[]),
        gebreken=[Gebrek(codering="GB1", omschrijving="Een scheur.", figuurnummer="")],
    )
    rak = Rak(rakdelen=[rakdeel], raknaam="TESTRAK", totale_lengte_m=12.0)

    async def classify_defect(defect: Gebrek) -> list[Gebrek]:
        return [ScheurHout(**defect.model_dump())]

    monkeypatch.setattr(
        RakdeelOmschrijving,
        "classificeer_omschrijving",
        AsyncMock(return_value=RakdeelOmschrijving(bouwjaar=2000, lengte_rakdeel=10.5)),
    )
    monkeypatch.setattr(Gebrek, "classify_gebrek", AsyncMock(side_effect=classify_defect))

    asyncio.run(process_rak(rak))

    assert rakdeel.bouwjaar == 1990
    assert rakdeel.lengte_m_omschrijving == 10.5
    assert isinstance(rakdeel.gebreken[0], ScheurHout)
    assert rakdeel.onderbouw.materiaal is NietBeschikbaar.LEEG
