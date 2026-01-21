from tekstherkenning_ark.llm.llm import AzureOpenAILLM
from tekstherkenning_ark.enums import MateriaalBovenbouw, MateriaalOnderbouw, MateriaalFundering, MateriaalVloer
from pydantic import BaseModel, Field
import os


class ConstructionDescription(BaseModel):
    bouwjaar: int | None
    lengte_rakdeel: int | None  # TODO: Verplaatsen naar

    # benodigd om type te bepalen
    materiaal_fundering: MateriaalFundering | None  # De fundering is alles onder de vloer, dus damwanden of palen.
    materiaal_onderbouw: MateriaalOnderbouw | None  # De onderbouw is ...
    materiaal_bovenbouw: MateriaalBovenbouw | None  # De bovenbouw is het dragende deel van de bovenbouw.
    # benodigd voor onderbouw/fundering
    materiaal_vloer: MateriaalVloer | None

    # onderloopsheidscherm aanwezig ja/nee
    onderloopsheidscherm: bool | None

    # benodigd voor constructie waterbodem
    bovenkant_deksteen_cm: int | None
    bovenkant_vloer_cm: int | None

if __name__ == "__main__":
    api_key = os.environ.get('AZURE_OPENAI_KEY')
    deployment = os.environ.get('DEPLOYMENT_NAME_GPT41') # Set to DEPLOYMENT_NAME_GPT4 for the GPT-4 model


    llm = AzureOpenAILLM(api_key, deployment)

    is_valid, message = llm.validate_api_key()
    print(message)




