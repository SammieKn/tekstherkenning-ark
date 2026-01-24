from tekstherkenning_ark.llm.llm import AzureOpenAILLM
from tekstherkenning_ark.enums import MateriaalBovenbouw, MateriaalOnderbouw, MateriaalFundering, MateriaalVloer, NietBeschikbaar
from pydantic import BaseModel, Field
import os
from typing import Annotated


class RakdeelOmschrijving(BaseModel):
    bouwjaar: int | None = Field(gt=1600, lt=2200, default=None, description="Bouwjaar van het rakdeel, houd leeg als onbekend.")
    
    # Lengte van het rakdeel, wordt gebruikt om de subdelen te toetsen in lengte tov totaal.
    lengte_rakdeel: float | None = Field(
        gt=0.0,
        default=None,
        description="Lengte van het rakdeel in meters, houd leeg als onbekend."
    )

    # Benodigd om type constructie te bepalen
    materiaal_fundering: MateriaalFundering | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Het materiaal van de fundering van het rakdeel. Dit is alles onder de vloer, bijvoorbeeld de palen of damwanden."
    )
    materiaal_onderbouw: MateriaalOnderbouw | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Het materiaal van de onderbouw van het rakdeel. Dit is alles tussen de fundering en de vloer."
    )
    materiaal_bovenbouw: MateriaalBovenbouw | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Het materiaal van de bovenbouw van het rakdeel. Dit is het verticale, dragende deel van de bovenbouw."
    )
    # benodigd voor onderbouw/fundering
    materiaal_vloer: MateriaalVloer | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Het materiaal van de vloer van het rakdeel."
    )

    # onderloopsheidscherm aanwezig ja/nee
    onderloopsheidscherm: bool | NietBeschikbaar = Field(
        default=NietBeschikbaar.LEEG,
        description="Geef aan of er een onderloopsheidscherm aanwezig is bij dit rakdeel door middel van boolean."
    )

    # benodigd voor constructie waterbodem
    bovenkant_deksteen_cm: float | None = Field(
        gt=0.0,
        default=None,
        description="De hoogte van de bovenkant van de kademuur in centimeters ten opzichte van de waterlijn. Ook wel kerende hoogte genoemd. De bovenkant wordt vaak aangegeven door deksteen, metselwerk of maaiveld."
    )
    bovenkant_vloer_cm: float | None = Field(
        gt=0.0,
        default=None,
        description="De hoogte van de waterlijn tot de bovenkant van de funderingsvloer. Als meerdere elementen onder de waterlijn worden vermeldt, dan tel je die op tot de vloer."
    )

if __name__ == "__main__":
    api_key = os.environ.get('AZURE_OPENAI_KEY')
    deployment = os.environ.get('DEPLOYMENT_NAME_GPT41') # Set to DEPLOYMENT_NAME_GPT4 for the GPT-4 model


    llm = AzureOpenAILLM(api_key, deployment)

    is_valid, message = llm.validate_api_key()
    print(message)




