from __future__ import annotations

from tekstherkenning_ark.llm.llm import AzureOpenAILLM
from tekstherkenning_ark.enums import (
    MateriaalBovenbouw,
    MateriaalOnderbouw,
    MateriaalFundering,
    MateriaalVloer,
    NietBeschikbaar,
)
from pydantic import BaseModel, Field
import os
from typing import Annotated


class RakdeelOmschrijving(BaseModel):
    bouwjaar: int | None = Field(
        gt=1600, lt=2200, default=None, description="Bouwjaar van het rakdeel, houd leeg als onbekend."
    )

    # Lengte van het rakdeel, wordt gebruikt om de subdelen te toetsen in lengte tov totaal.
    lengte_rakdeel: float | None = Field(
        gt=0.0, default=None, description="Lengte van het rakdeel in meters, houd leeg als onbekend."
    )

    # Benodigd om type constructie te bepalen
    materiaal_fundering: MateriaalFundering | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Het materiaal van de fundering van het rakdeel. Dit is alles onder de vloer, bijvoorbeeld de palen of damwanden.",
    )
    materiaal_onderbouw: MateriaalOnderbouw | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Het materiaal van de onderbouw van het rakdeel. Dit is alles tussen de fundering en de vloer.",
    )
    materiaal_bovenbouw: MateriaalBovenbouw | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Het materiaal van de bovenbouw van het rakdeel. Dit is het verticale, dragende deel van de bovenbouw.",
    )
    # benodigd voor onderbouw/fundering
    materiaal_vloer: MateriaalVloer | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG, description="Het materiaal van de vloer van het rakdeel."
    )

    # onderloopsheidscherm aanwezig ja/nee
    onderloopsheidscherm: bool | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Geef aan of er een onderloopsheidscherm aanwezig is bij dit rakdeel door middel van boolean.",
    )

    # benodigd voor constructie waterbodem
    bovenkant_deksteen_cm: float | None = Field(
        gt=0.0,
        default=None,
        description="De hoogte van de bovenkant van de kademuur in centimeters ten opzichte van de waterlijn. Ook wel kerende hoogte genoemd. De bovenkant wordt vaak aangegeven door deksteen, metselwerk of maaiveld.",
    )
    bovenkant_vloer_cm: float | None = Field(
        gt=0.0,
        default=None,
        description="De hoogte van de waterlijn tot de bovenkant van de funderingsvloer. Als meerdere elementen onder de waterlijn worden vermeldt, dan tel je die op tot de vloer.",
    )

    @classmethod
    def classificeer_omschrijving(cls, omschrijving: str) -> RakdeelOmschrijving:
        """
        Classificeer een omschrijving naar een RakdeelOmschrijving instance via Azure OpenAI.

        Parameters
        ----------
        llm : AzureOpenAILLM
            De Azure OpenAI LLM instantie.
        omschrijving : str
            De omschrijving tekst om te classificeren.

        Returns
        -------
        RakdeelOmschrijving
            Het geclassificeerde RakdeelOmschrijving object.
        """
        llm = AzureOpenAILLM()

        system_prompt = """Je bent een expert in het analyseren van constructie-omschrijvingen van kademuren.
            Extraheer de relevante informatie uit de omschrijving en vul de velden in.
            Laat velden leeg of op NietBeschikbaar.LEEG als de informatie niet beschikbaar is."""

        print("Classificeren van rakdeel omschrijving via LLM...")
        response = llm.client.beta.chat.completions.parse(
            model=llm.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Classificeer de volgende omschrijving:\n\n{omschrijving}"},
            ],
            response_format=RakdeelOmschrijving,
            temperature=0,
        )

        parsed_result = response.choices[0].message.parsed
        if parsed_result is None:
            raise ValueError("Kon de omschrijving niet classificeren: geen resultaat ontvangen van LLM")
        else:
            return parsed_result
