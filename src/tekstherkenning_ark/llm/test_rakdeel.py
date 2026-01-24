"""
Jij gaat helpen met het schrijven van code dat door middel van input data regel bij regel de tekst gaat classificeren naar het RakdeelOmschrijving model.
Hiervoor gebruik je de Azure OpenAI LLM klas en definieer je een response format type (text_format?) naar RakdeelOmschrijving.
Het doel is dat wij rackdeelondrijving instances terugkrijgen van het model. Per rij.
Voor iedere rij in de testset klassificer je de omschrijving naar de RakdeelOmschrijving.
Op het einde zet je de dataset weer om van rackdeelomschrijving naar een dataframe voor verdere checks.
Limiteer dat script tot de eerste tien regels.

"""
import os
from datetime import datetime
from tekstherkenning_ark.llm.rakdeel_omschrijving import RakdeelOmschrijving
from tekstherkenning_ark.llm.llm import AzureOpenAILLM
from tekstherkenning_ark.constants import DATA_DIR
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

TESTDATA_PATH = DATA_DIR / Path("constructie_omschrijvingen_testset.xlsx")
constructie_omschrijving = pd.read_excel(TESTDATA_PATH, sheet_name="rakdeel_omschrijving")
df_test = constructie_omschrijving[["rak", "rakdeel", "omschrijving"]]

def classificeer_omschrijving(llm: AzureOpenAILLM, omschrijving: str) -> RakdeelOmschrijving:
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
    system_prompt = """Je bent een expert in het analyseren van constructie-omschrijvingen van kademuren.
Extraheer de relevante informatie uit de omschrijving en vul de velden in.
Laat velden leeg of op NietBeschikbaar.LEEG als de informatie niet beschikbaar is."""

    response = llm.client.beta.chat.completions.parse(
        model=llm.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Classificeer de volgende omschrijving:\n\n{omschrijving}"}
        ],
        response_format=RakdeelOmschrijving,
        temperature=0
    )
    
    parsed_result = response.choices[0].message.parsed
    if parsed_result is None:
        raise ValueError("Kon de omschrijving niet classificeren: geen resultaat ontvangen van LLM")
    
    return parsed_result


def verwerk_testset(llm: AzureOpenAILLM, df_origineel: pd.DataFrame, max_rijen: int = 10) -> pd.DataFrame:
    """
    Verwerk de testset en classificeer elke omschrijving.
    
    Parameters
    ----------
    llm : AzureOpenAILLM
        De Azure OpenAI LLM instantie.
    df_origineel : pd.DataFrame
        Originele DataFrame met constructie omschrijvingen.
    max_rijen : int
        Maximum aantal rijen om te verwerken.
        
    Returns
    -------
    pd.DataFrame
        Originele DataFrame aangevuld met LLM_ kolommen.
    """
    df = df_origineel.head(max_rijen).copy()
    llm_kolommen = {f"LLM_{veld}": [] for veld in RakdeelOmschrijving.model_fields.keys()}
    
    for idx, (_, rij) in enumerate(df.iterrows(), start=1):
        print(f"Verwerken rij {idx}/{len(df)}: {rij['rak']} - {rij['rakdeel']}")
        
        rakdeel_info = classificeer_omschrijving(llm, rij["omschrijving"])
        
        # Voeg LLM resultaten toe aan de kolommen
        for veld, waarde in rakdeel_info.model_dump().items():
            llm_kolommen[f"LLM_{veld}"].append(waarde)
    
    # Voeg LLM kolommen toe aan originele DataFrame
    for kolom, waarden in llm_kolommen.items():
        df[kolom] = waarden
    
    return df


if __name__ == "__main__":
    load_dotenv()
    api_key = os.environ.get('AZURE_OPENAI_KEY')
    deployment = os.environ.get('DEPLOYMENT_NAME_GPT41')

    llm = AzureOpenAILLM(api_key, deployment)

    is_valid, message = llm.validate_api_key()
    print(message)
    
    if is_valid:
        # Verwerk de eerste 10 rijen van de testset
        df_resultaat = verwerk_testset(llm, constructie_omschrijving, max_rijen=14)
        
        print("\n=== Resultaten ===")
        print(df_resultaat.to_string())
        
        # Opslaan naar Excel met timestamp
        output_dir = DATA_DIR / "rakdeel_omschrijving"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"rakdeel_resultaten_{timestamp}.xlsx"
        df_resultaat.to_excel(output_path, index=False)
        print(f"\nResultaten opgeslagen naar: {output_path}")
