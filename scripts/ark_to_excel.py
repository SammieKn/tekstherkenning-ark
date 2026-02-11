"""
ARK Excel naar Testdata Parser
==============================

Dit script parseert ARK Excel-bestanden en extraheert testdata voor validatie van onze
parsing methodes in de `models/` map.

De testdata bevindt zich in de sheet "ARK". Elk rij representeert één rakdeel.

Uitgesloten kolommen (niet relevant voor testdata):
- Belastingen op kade muur
- Resultaten toestand constructie
- Controle
- Advies

Eerste test is gericht op rak `HEG0201`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from tekstherkenning_ark.constants import DATA_DIR
from tekstherkenning_ark.enums import (
    MateriaalBovenbouw,
    MateriaalFundering,
    MateriaalOnderbouw,
)

# Lokale implementatie van get_rak_id om circulaire import te voorkomen
# TODO: Weghalen na oplossing circulaire import - Matthias
RAK_ID_PATTERN = r"([A-Z]{3}\d{4})(-\d{2})?"


def get_rak_id(value: str) -> str | None:
    """Extraheer rak ID uit een string (bijv. ABC1234, DEF5678-01).

    Parameters
    ----------
    value : str
        Input string die mogelijk een rak ID bevat.

    Returns
    -------
    str | None
        Het geëxtraheerde rak ID of None indien niet gevonden.
    """
    if not isinstance(value, str):
        return None
    match = re.search(RAK_ID_PATTERN, value.strip())
    return match.group(0) if match else None


# ==============================================================================
# Kolom mapping definities
# ==============================================================================


def _parse_ja_nee(waarde: Any) -> bool | None:
    """Converteer Ja/Nee waarde naar boolean.

    Parameters
    ----------
    waarde : Any
        De te parsen waarde.

    Returns
    -------
    bool | None
        True voor "Ja", False voor "Nee", None voor overige waarden.
    """
    if pd.isna(waarde):
        return None
    waarde_str = str(waarde).strip().lower()
    if waarde_str in ("ja", "j", "yes", "y", "1"):
        return True
    if waarde_str in ("nee", "n", "no", "0"):
        return False
    return None


def _parse_materiaal_bovenbouw(waarde: Any) -> MateriaalBovenbouw | None:
    """Converteer materiaal bovenbouw string naar enum.

    Parameters
    ----------
    waarde : Any
        De te parsen waarde.

    Returns
    -------
    MateriaalBovenbouw | None
        De geconverteerde enum waarde of None.
    """
    if pd.isna(waarde):
        return None
    waarde_str = str(waarde).strip()
    # Mapping voor veelvoorkomende variaties
    mapping = {
        "Metselwerk (baksteen)": MateriaalBovenbouw.METSELWERK,
        "Metselwerk": MateriaalBovenbouw.METSELWERK,
        "Basalt (blokken)": MateriaalBovenbouw.BASALT,
        "Beton": MateriaalBovenbouw.BETON,
        "Beton met metselwerk": MateriaalBovenbouw.BETON_METSELWERK,
        "Beton+Metselwerk": MateriaalBovenbouw.BETON_METSELWERK,
        "Beton+Basalt": MateriaalBovenbouw.BETON_BASALT,
    }
    return mapping.get(waarde_str)


def _veilige_float(waarde: Any) -> float | None:
    """Veilig converteren naar float, geeft None bij ongeldige waarden.

    Parameters
    ----------
    waarde : Any
        De te converteren waarde.

    Returns
    -------
    float | None
        De float waarde of None bij ongeldige input.
    """
    if pd.isna(waarde):
        return None
    if isinstance(waarde, (int, float)):
        return float(waarde)
    try:
        return float(waarde)
    except (ValueError, TypeError):
        return None


def _veilige_int(waarde: Any) -> int | None:
    """Veilig converteren naar int, geeft None bij ongeldige waarden.

    Parameters
    ----------
    waarde : Any
        De te converteren waarde.

    Returns
    -------
    int | None
        De int waarde of None bij ongeldige input.
    """
    if pd.isna(waarde):
        return None
    if isinstance(waarde, int):
        return waarde
    if isinstance(waarde, float):
        return int(waarde)
    try:
        return int(float(waarde))
    except (ValueError, TypeError):
        return None


@dataclass
class KolomMapping:
    """Mapping tussen Excel kolomnummer en datamodel veld.

    Attributes
    ----------
    kolom_index : int
        Nul-gebaseerde kolomindex in het Excel bestand.
    excel_naam : str
        Naam van de kolom zoals in de Excel header.
    datamodel_veld : str
        Corresponderende veld in het datamodel (pad notatie, bijv. "bovenbouw.materiaal").
    datatype : type
        Verwacht datatype van de waarde.
    conversie_functie : callable, optioneel
        Functie om de Excel waarde te converteren naar het juiste type.
    """

    kolom_index: int
    excel_naam: str
    datamodel_veld: str
    datatype: type = str
    conversie_functie: Callable[[Any], Any] | None = None


# Excel kolom mappings naar datamodel velden
# Gebaseerd op analyse van HEG0201 ARK Excel bestand
ARK_KOLOM_MAPPINGS: list[KolomMapping] = [
    # Algemene rak informatie
    KolomMapping(
        kolom_index=0,
        excel_naam="Rak(deel) code",
        datamodel_veld="rakdeel.rakdeel_id",
        datatype=str,
    ),
    KolomMapping(
        kolom_index=1,
        excel_naam="Objecttype",
        datamodel_veld="rakdeel.objecttype",
        datatype=str,
    ),
    KolomMapping(
        kolom_index=2,
        excel_naam="Aantal Rakdelen",
        datamodel_veld="rak.aantal_rakdelen",
        datatype=int,
    ),
    # Materialen
    KolomMapping(
        kolom_index=3,
        excel_naam="Materiaal Fundering",
        datamodel_veld="onderbouw.materiaal_fundering",
        datatype=MateriaalFundering,
        conversie_functie=lambda x: MateriaalFundering(x) if pd.notna(x) else str(x),
    ),
    KolomMapping(
        kolom_index=4,
        excel_naam="Materiaal Onderbouw",
        datamodel_veld="onderbouw.materiaal_onderbouw",
        datatype=MateriaalOnderbouw,
        conversie_functie=lambda x: MateriaalOnderbouw(x) if pd.notna(x) else str(x),
    ),
    KolomMapping(
        kolom_index=5,
        excel_naam="Materiaal Bovenbouw",
        datamodel_veld="bovenbouw.materiaal_bovenbouw",
        datatype=MateriaalBovenbouw,
        conversie_functie=_parse_materiaal_bovenbouw,
    ),
    # Constructie informatie
    KolomMapping(
        kolom_index=13,
        excel_naam="Type constructie",
        datamodel_veld="rakdeel.constructietype",
        datatype=str,
    ),
    KolomMapping(
        kolom_index=14,
        excel_naam="Bouwjaar bekend?",
        datamodel_veld="rakdeel.bouwjaar_bekend",
        datatype=bool,
        conversie_functie=_parse_ja_nee,
    ),
    KolomMapping(
        kolom_index=15,
        excel_naam="Bouwjaar",
        datamodel_veld="rakdeel.bouwjaar",
        datatype=int,
        conversie_functie=_veilige_int,
    ),
    # Bovenbouw indicator velden
    KolomMapping(
        kolom_index=86,
        excel_naam="Bovenkant deksteen",
        datamodel_veld="bovenbouw.bovenkant_deksteen_cm_tov_nap",
        datatype=float,
        conversie_functie=lambda x: _veilige_float(x) * 100 if _veilige_float(x) is not None else None,  # m naar cm
    ),
    KolomMapping(
        kolom_index=112,
        excel_naam="Aantal scheuren rakdeel",
        datamodel_veld="bovenbouw.aantal_scheuren",
        datatype=int,
        conversie_functie=_veilige_int,
    ),
    KolomMapping(
        kolom_index=116,
        excel_naam="Max. Aantal scheuren per 10 m",
        datamodel_veld="bovenbouw.maximaal_aantal_scheuren_per_10_m",
        datatype=int,
        conversie_functie=_veilige_int,
    ),
    KolomMapping(
        kolom_index=119,
        excel_naam="Maatgevende scheurwijdte",
        datamodel_veld="bovenbouw.maximale_scheurwijdte_mm",
        datatype=float,
        conversie_functie=_veilige_float,
    ),
    KolomMapping(
        kolom_index=121,
        excel_naam="Lokaal verdwenen metselwerk",
        datamodel_veld="bovenbouw.is_lokaal_verdwenen_metselwerk",
        datatype=bool,
        conversie_functie=_parse_ja_nee,
    ),
    KolomMapping(
        kolom_index=122,
        excel_naam="Gat grondvoerend",
        datamodel_veld="bovenbouw.is_grondvoerend_gat_aanwezig",
        datatype=bool,
        conversie_functie=_parse_ja_nee,
    ),
    KolomMapping(
        kolom_index=124,
        excel_naam="Buik in wand",
        datamodel_veld="bovenbouw.is_buik_in_wand_aanwezig",
        datatype=bool,
        conversie_functie=_parse_ja_nee,
    ),
    KolomMapping(
        kolom_index=125,
        excel_naam="Scheur t.p.v. buik aanwezig",
        datamodel_veld="bovenbouw.is_scheur_t_p_v_buik_aanwezig",
        datatype=bool,
        conversie_functie=_parse_ja_nee,
    ),
    KolomMapping(
        kolom_index=127,
        excel_naam="Scheefstand wand",
        datamodel_veld="bovenbouw.is_scheefstand_aanwezig",
        datatype=bool,
        conversie_functie=_parse_ja_nee,
    ),
    KolomMapping(
        kolom_index=128,
        excel_naam="Scheur bij scheefstand wand",
        datamodel_veld="bovenbouw.scheur_bij_scheefstand_aanwezig",
        datatype=bool,
        conversie_functie=_parse_ja_nee,
    ),
    KolomMapping(
        kolom_index=130,
        excel_naam="Niet functionerend schuifhout",
        datamodel_veld="bovenbouw.percentage_niet_functionerend_schuifhout",
        datatype=float,
        conversie_functie=_veilige_float,
    ),
    # Onderbouw indicator velden
    KolomMapping(
        kolom_index=87,
        excel_naam="niveau bovenkanst vloer",
        datamodel_veld="vloer.bovenkant_vloer_cm_tov_nap",
        datatype=float,
        conversie_functie=lambda x: _veilige_float(x) * 100 if _veilige_float(x) is not None else None,  # m naar cm
    ),
    KolomMapping(
        kolom_index=92,
        excel_naam="Percentage slechte houten palen",
        datamodel_veld="onderbouw.percentage_slechte_palen",
        datatype=float,
        conversie_functie=_veilige_float,
    ),
    KolomMapping(
        kolom_index=94,
        excel_naam="Ongewenste schoorstand funderingspalen",
        datamodel_veld="onderbouw.percentage_ongewenste_schoorstand",
        datatype=float,
        conversie_functie=_veilige_float,
    ),
    KolomMapping(
        kolom_index=96,
        excel_naam="Percentage beschadigde kespen",
        datamodel_veld="onderbouw.percentage_beschadigde_kespen",
        datatype=float,
        conversie_functie=_veilige_float,
    ),
    KolomMapping(
        kolom_index=98,
        excel_naam="Percentage beschadigde verbinding",
        datamodel_veld="onderbouw.percentage_beschadigde_verbinding",
        datatype=float,
        conversie_functie=_veilige_float,
    ),
    KolomMapping(
        kolom_index=100,
        excel_naam="Materiaal vloer",
        datamodel_veld="onderbouw.vloer.materiaal",
        datatype=str,
    ),
    KolomMapping(
        kolom_index=101,
        excel_naam="Vloer beschadigd",
        datamodel_veld="onderbouw.vloer.is_beschadigd",
        datatype=bool,
        conversie_functie=_parse_ja_nee,
    ),
    KolomMapping(
        kolom_index=106,
        excel_naam="Onderloopsheidscherm aanwezig",
        datamodel_veld="onderbouw.onderloopsheidscherm.is_aanwezig",
        datatype=bool,
        conversie_functie=_parse_ja_nee,
    ),
    KolomMapping(
        kolom_index=107,
        excel_naam="Onderloopsheidscherm beschadigd",
        datamodel_veld="onderbouw.onderloopsheidscherm.is_beschadigd",
        datatype=bool,
        conversie_functie=_parse_ja_nee,
    ),
    # Rakdeel lengte
    KolomMapping(
        kolom_index=184,
        excel_naam="Lengte Rakdeel",
        datamodel_veld="lengte_rakdeel_m",
        datatype=float,
        conversie_functie=_veilige_float,
    ),
]


# ==============================================================================
# Testdata dataklasse
# ==============================================================================


@dataclass
class RakdeelTestData:
    """Container voor geëxtraheerde testdata van een rakdeel uit ARK Excel.

    Attributes
    ----------
    rakdeel_id : str
        Unieke identifier van het rakdeel (bijv. "HEG0201-A").
    rak_id : str
        Identifier van het rak (bijv. "HEG0201").
    ruwe_data : dict[str, Any]
        Dictionary met alle geëxtraheerde velden en hun waarden.
    """

    rakdeel_id: str
    rak_id: str
    ruwe_data: dict[str, Any] = field(default_factory=dict)

    def get_veld(self, datamodel_pad: str) -> Any:
        """Haal een waarde op via het datamodel pad.

        Parameters
        ----------
        datamodel_pad : str
            Het pad naar het veld (bijv. "bovenbouw.materiaal").

        Returns
        -------
        Any
            De waarde van het veld of None als niet gevonden.
        """
        return self.ruwe_data.get(datamodel_pad)

    def __repr__(self) -> str:
        """Tekstuele representatie van de testdata."""
        return f"RakdeelTestData(rakdeel_id={self.rakdeel_id!r}, velden={len(self.ruwe_data)})"


# ==============================================================================
# Excel parser klasse
# ==============================================================================


class ArkExcelParser:
    """Parser voor ARK Excel bestanden.

    Parameters
    ----------
    excel_pad : Path
        Pad naar het ARK Excel bestand.

    Attributes
    ----------
    excel_pad : Path
        Pad naar het Excel bestand.
    df : pd.DataFrame | None
        Geladen DataFrame of None als nog niet geladen.
    """

    # Constanten voor de ARK sheet structuur
    SHEET_NAAM = "ARK"
    HEADER_RIJ_1 = 5  # Eerste header rij (nul-gebaseerd)
    HEADER_RIJ_2 = 6  # Tweede header rij
    DATA_START_RIJ = 9  # Eerste data rij

    def __init__(self, excel_pad: Path):
        """Initialiseer de parser.

        Parameters
        ----------
        excel_pad : Path
            Pad naar het ARK Excel bestand.
        """
        self.excel_pad = excel_pad
        self.df: pd.DataFrame | None = None

    def laad_data(self) -> pd.DataFrame:
        """Laad de ARK sheet uit het Excel bestand.

        Returns
        -------
        pd.DataFrame
            De geladen DataFrame.

        Raises
        ------
        FileNotFoundError
            Als het Excel bestand niet bestaat.
        ValueError
            Als de ARK sheet niet gevonden wordt.
        """
        if not self.excel_pad.exists():
            raise FileNotFoundError(f"Excel bestand niet gevonden: {self.excel_pad}")

        try:
            self.df = pd.read_excel(
                self.excel_pad,
                sheet_name=self.SHEET_NAAM,
                header=None,
            )
        except ValueError as e:
            raise ValueError(f"Sheet '{self.SHEET_NAAM}' niet gevonden in {self.excel_pad}") from e

        return self.df

    def extraheer_rakdeel_data(self, rij_index: int) -> RakdeelTestData | None:
        """Extraheer testdata voor een specifieke rij (rakdeel).

        Parameters
        ----------
        rij_index : int
            De rij-index in de DataFrame (nul-gebaseerd).

        Returns
        -------
        RakdeelTestData | None
            De geëxtraheerde testdata of None als de rij geen geldig rakdeel bevat.
        """
        if self.df is None:
            self.laad_data()

        assert self.df is not None  # Voor type checker
        rij = self.df.iloc[rij_index]

        # Haal rakdeel_id op (kolom 0)
        rakdeel_id = rij.iloc[0]
        if pd.isna(rakdeel_id) or not isinstance(rakdeel_id, str):
            return None

        # Extraheer rak_id uit rakdeel_id
        rak_id = get_rak_id(rakdeel_id)
        if rak_id is None:
            return None

        # Extraheer alle velden volgens de mapping
        ruwe_data: dict[str, Any] = {}
        for mapping in ARK_KOLOM_MAPPINGS:
            waarde = rij.iloc[mapping.kolom_index]
            if mapping.conversie_functie:
                waarde = mapping.conversie_functie(waarde)
            elif pd.isna(waarde):
                waarde = None
            ruwe_data[mapping.datamodel_veld] = waarde

        return RakdeelTestData(
            rakdeel_id=rakdeel_id,
            rak_id=rak_id,
            ruwe_data=ruwe_data,
        )

    def extraheer_alle_rakdelen(self) -> list[RakdeelTestData]:
        """Extraheer testdata voor alle rakdelen in de Excel.

        Returns
        -------
        list[RakdeelTestData]
            Lijst met testdata voor elk gevonden rakdeel.
        """
        if self.df is None:
            self.laad_data()

        assert self.df is not None  # Voor type checker
        resultaten: list[RakdeelTestData] = []
        for rij_index in range(self.DATA_START_RIJ, len(self.df)):
            testdata = self.extraheer_rakdeel_data(rij_index)
            if testdata:
                resultaten.append(testdata)

        return resultaten

    def filter_op_rak_id(self, rak_id: str) -> list[RakdeelTestData]:
        """Filter rakdelen op rak_id.

        Parameters
        ----------
        rak_id : str
            De rak identifier om op te filteren (bijv. "HEG0201").

        Returns
        -------
        list[RakdeelTestData]
            Lijst met rakdelen die bij het rak horen.
        """
        alle_rakdelen = self.extraheer_alle_rakdelen()
        return [rd for rd in alle_rakdelen if rd.rak_id == rak_id]


# ==============================================================================
# Hulpfuncties
# ==============================================================================


def vind_ark_excel_voor_rak(rak_id: str) -> Path | None:
    ark_path = DATA_DIR / "ark"
    for excel_bestand in ark_path.glob("*.xlsm"):
        if rak_id in excel_bestand.stem:
            return excel_bestand
    return None


def laad_testdata_voor_rak(rak_id: str) -> list[RakdeelTestData]:
    excel_pad = vind_ark_excel_voor_rak(rak_id)
    if excel_pad is None:
        raise FileNotFoundError(f"Geen ARK Excel bestand gevonden voor rak: {rak_id}")

    parser = ArkExcelParser(excel_pad)
    return parser.filter_op_rak_id(rak_id)


def vind_alle_ark_excels() -> list[Path]:
    ark_path = DATA_DIR / "ark"
    # Filter tijdelijke bestanden (beginnen met ~$)
    ark_excels = [f for f in ark_path.glob("*.xlsm") if not f.name.startswith("~$")]
    if not ark_excels:
        raise FileNotFoundError(f"Geen ARK Excel bestanden gevonden in: {ark_path}")
    return ark_excels


def laad_alle_testdata() -> list[RakdeelTestData]:
    alle_testdata: list[RakdeelTestData] = []

    for excel_pad in vind_alle_ark_excels():
        print(f"Verwerken: {excel_pad.name}")
        try:
            parser = ArkExcelParser(excel_pad)
            rakdelen = parser.extraheer_alle_rakdelen()
            alle_testdata.extend(rakdelen)
            print(f"  -> {len(rakdelen)} rakdelen gevonden")
        except Exception as e:
            print(f"  -> Fout bij verwerken: {e}")

    return alle_testdata


def exporteer_naar_excel(testdata_lijst: list[RakdeelTestData], uitvoer_pad: Path) -> None:
    """Exporteer alle testdata naar een Excel bestand.

    Parameters
    ----------
    testdata_lijst : list[RakdeelTestData]
        Lijst met testdata om te exporteren.
    uitvoer_pad : Path
        Pad naar het uitvoer Excel bestand.
    """
    # Maak een lijst van dictionaries voor de DataFrame
    rijen: list[dict[str, Any]] = []

    for testdata in testdata_lijst:
        rij: dict[str, Any] = {
            "rak_id": testdata.rak_id,
            "rakdeel_id": testdata.rakdeel_id,
        }
        # Voeg alle velden uit ruwe_data toe
        for veld, waarde in testdata.ruwe_data.items():
            # Converteer enum waarden naar strings voor Excel
            if hasattr(waarde, "value"):
                waarde = waarde.value
            rij[veld] = waarde
        rijen.append(rij)

    # Maak DataFrame en exporteer
    df = pd.DataFrame(rijen)

    # Sorteer kolommen: eerst rak_id en rakdeel_id, dan de rest alfabetisch
    vaste_kolommen = ["rak_id", "rakdeel_id"]
    overige_kolommen = sorted([k for k in df.columns if k not in vaste_kolommen])
    df = df[vaste_kolommen + overige_kolommen]

    # Maak output directory als deze niet bestaat
    uitvoer_pad.parent.mkdir(parents=True, exist_ok=True)

    # Exporteer naar Excel
    df.to_excel(uitvoer_pad, index=False, sheet_name="Testdata")
    print(f"\nGeëxporteerd naar: {uitvoer_pad}")
    print(f"Totaal aantal rakdelen: {len(df)}")


# ==============================================================================
# Main uitvoering
# ==============================================================================


if __name__ == "__main__":
    print("=" * 60)
    print("ARK Excel Testdata Extractor")
    print("=" * 60)

    # Laad alle testdata uit alle ARK Excel bestanden
    print("\nStap 1: Laden van alle ARK Excel bestanden...")
    alle_testdata = laad_alle_testdata()

    # Exporteer naar testset.xlsx
    print("\nStap 2: Exporteren naar Excel...")
    uitvoer_pad = DATA_DIR / "ark" / "testset.xlsx"
    exporteer_naar_excel(alle_testdata, uitvoer_pad)

    print("\n" + "=" * 60)
    print("Klaar!")
    print("=" * 60)
