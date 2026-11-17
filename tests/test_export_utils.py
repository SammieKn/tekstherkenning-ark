import pandas as pd
from openpyxl import load_workbook

from tekstherkenning_ark.export_utils import remove_unsafe_values_for_excel


def test_excelveilige_dataframe_verwijdert_xml_ongeldige_tekens(tmp_path):
    """Controleer dat opgeschoonde DataFrames veilig naar een leesbaar Excel-bestand schrijven."""
    dataframe = pd.DataFrame({"kop\ufffe": ["tekst\x00\ufffe\ud800", "behouden\ttekst"]})

    veilig_dataframe = remove_unsafe_values_for_excel(dataframe)
    excel_pad = tmp_path / "uitvoer.xlsx"
    veilig_dataframe.to_excel(excel_pad, engine="openpyxl", index=False)

    werkboek = load_workbook(excel_pad)
    werkblad = werkboek.active

    assert werkblad["A1"].value == "kop"
    assert werkblad["A2"].value == "tekst"
    assert werkblad["A3"].value == "behouden\ttekst"
    assert dataframe.columns[0] == "kop\ufffe"
