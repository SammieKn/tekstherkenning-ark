import os
import asyncio
from datetime import datetime
from tekstherkenning_ark.llm.rakdeel_omschrijving import RakdeelOmschrijving
from tekstherkenning_ark.llm.azureopenaillm import AzureOpenAILLM
from tekstherkenning_ark.constants import DATA_DIR
from pathlib import Path
import pandas as pd

TESTDATA_PATH = DATA_DIR / Path("constructie_omschrijvingen_testset.xlsx")
constructie_omschrijving = pd.read_excel(TESTDATA_PATH, sheet_name="rakdeel_omschrijving")
df_test = constructie_omschrijving[["rak", "rakdeel", "omschrijving"]]


async def verwerk_testset(df_origineel: pd.DataFrame, max_rijen: int = 10) -> pd.DataFrame:
    """
    Verwerk de testset en classificeer elke omschrijving.

    Parameters
    ----------
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

        rakdeel_info = await RakdeelOmschrijving.classificeer_omschrijving(rij["omschrijving"])

        # Voeg LLM resultaten toe aan de kolommen
        for veld, waarde in rakdeel_info.model_dump().items():
            llm_kolommen[f"LLM_{veld}"].append(waarde)

    # Voeg LLM kolommen toe aan originele DataFrame
    for kolom, waarden in llm_kolommen.items():
        df[kolom] = waarden

    return df


async def main():
    async with AzureOpenAILLM() as llm:
        is_valid, message = await llm.validate_api_key()
        print(message)

        if is_valid:
            # Verwerk de eerste 10 rijen van de testset
            df_resultaat = await verwerk_testset(constructie_omschrijving, max_rijen=14)

        print("\n=== Resultaten ===")
            print("\n=== Resultaten ===")
            print(df_resultaat.to_string())

            # Opslaan naar Excel met timestamp
            output_dir = DATA_DIR / "rakdeel_omschrijving"
            output_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"rakdeel_resultaten_{timestamp}.xlsx"
            df_resultaat.to_excel(output_path, index=False)
            print(f"\nResultaten opgeslagen naar: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())