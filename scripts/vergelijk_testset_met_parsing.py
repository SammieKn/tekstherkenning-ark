"""
Testset Vergelijking Script
============================

Dit script vergelijkt de data uit testset.xlsx (ground truth) met de geparsede
Rak objecten uit onze parsing pipeline.

Output:
- Excel bestand met kleuren die aangeven of waarden correct zijn
  - Lichtgroen: waarden komen overeen
  - Rood: waarden komen niet overeen
  - Geel: waarde ontbreekt in één van beide
  - Wit: waarde ontbreekt in beide
- Console output met statistieken

Gebruik:
    python scripts/vergelijk_testset_met_parsing.py
"""

from __future__ import annotations

import pickle
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows

from tekstherkenning_ark.constants import CACHE_DIR, DATA_DIR
from tekstherkenning_ark.enums import (
    MateriaalBovenbouw,
    MateriaalFundering,
    MateriaalOnderbouw,
)
from tekstherkenning_ark.models.rak import Rak
from ark_to_excel import ARK_KOLOM_MAPPINGS, KolomMapping


# ==============================================================================
# Kleuren voor Excel output
# ==============================================================================

KLEUR_CORRECT = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")  # Lichtgroen
KLEUR_FOUT = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")  # Rood
KLEUR_ONTBREEKT = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")  # Geel
# Wit wordt automatisch gebruikt (geen fill)


# ==============================================================================
# Vergelijkingsresultaat dataklassen
# ==============================================================================


@dataclass
class VeldVergelijking:
    """Resultaat van één veld vergelijking.

    Attributes
    ----------
    veld_naam : str
        Naam van het veld (datamodel pad).
    verwacht : Any
        Verwachte waarde uit testset.
    gekregen : Any
        Gekregen waarde uit parsing.
    is_correct : bool | None
        True als waarden overeenkomen, False als niet, None als één of beide missing.
    """

    veld_naam: str
    verwacht: Any
    gekregen: Any
    is_correct: bool | None


@dataclass
class RakdeelVergelijking:
    """Vergelijkingsresultaat voor één rakdeel.

    Attributes
    ----------
    rak_id : str
        RAK identifier.
    rakdeel_id : str
        Rakdeel identifier.
    veld_vergelijkingen : list[VeldVergelijking]
        Lijst met vergelijkingen per veld.
    """

    rak_id: str
    rakdeel_id: str
    veld_vergelijkingen: list[VeldVergelijking] = field(default_factory=list)

    @property
    def aantal_correct(self) -> int:
        """Aantal correcte velden."""
        return sum(1 for vv in self.veld_vergelijkingen if vv.is_correct is True)

    @property
    def aantal_fout(self) -> int:
        """Aantal foute velden."""
        return sum(1 for vv in self.veld_vergelijkingen if vv.is_correct is False)

    @property
    def aantal_ontbrekend(self) -> int:
        """Aantal ontbrekende velden (in één of beide)."""
        return sum(1 for vv in self.veld_vergelijkingen if vv.is_correct is None)

    @property
    def totaal_velden(self) -> int:
        """Totaal aantal velden."""
        return len(self.veld_vergelijkingen)

    @property
    def accuratie_percentage(self) -> float:
        """Accuratie percentage (alleen correcte en foute velden tellen mee)."""
        vergelijkbare = self.aantal_correct + self.aantal_fout
        if vergelijkbare == 0:
            return 0.0
        return round((self.aantal_correct / vergelijkbare) * 100, 2)


@dataclass
class VergelijkingsStatistieken:
    """Verzamel statistieken voor alle vergelijkingen.

    Attributes
    ----------
    rakdeel_vergelijkingen : list[RakdeelVergelijking]
        Lijst van alle rakdeel vergelijkingen.
    """

    rakdeel_vergelijkingen: list[RakdeelVergelijking] = field(default_factory=list)

    @property
    def totaal_rakdelen(self) -> int:
        """Totaal aantal vergeleken rakdelen."""
        return len(self.rakdeel_vergelijkingen)

    @property
    def totaal_velden(self) -> int:
        """Totaal aantal vergeleken velden over alle rakdelen."""
        return sum(rv.totaal_velden for rv in self.rakdeel_vergelijkingen)

    @property
    def totaal_correct(self) -> int:
        """Totaal aantal correcte velden."""
        return sum(rv.aantal_correct for rv in self.rakdeel_vergelijkingen)

    @property
    def totaal_fout(self) -> int:
        """Totaal aantal foute velden."""
        return sum(rv.aantal_fout for rv in self.rakdeel_vergelijkingen)

    @property
    def totaal_ontbrekend(self) -> int:
        """Totaal aantal ontbrekende velden."""
        return sum(rv.aantal_ontbrekend for rv in self.rakdeel_vergelijkingen)

    @property
    def gemiddelde_accuratie(self) -> float:
        """Gemiddelde accuratie over alle rakdelen."""
        if not self.rakdeel_vergelijkingen:
            return 0.0
        accuracies = [rv.accuratie_percentage for rv in self.rakdeel_vergelijkingen]
        return round(sum(accuracies) / len(accuracies), 2)

    def statistieken_per_veld(self) -> dict[str, dict[str, int | float]]:
        """Bereken statistieken per veld type.

        Returns
        -------
        dict[str, dict[str, int | float]]
            Dictionary met per veld naam de statistieken.
        """
        veld_stats: dict[str, dict[str, int]] = {}

        for rv in self.rakdeel_vergelijkingen:
            for vv in rv.veld_vergelijkingen:
                if vv.veld_naam not in veld_stats:
                    veld_stats[vv.veld_naam] = {"correct": 0, "fout": 0, "ontbrekend": 0}

                if vv.is_correct is True:
                    veld_stats[vv.veld_naam]["correct"] += 1
                elif vv.is_correct is False:
                    veld_stats[vv.veld_naam]["fout"] += 1
                else:
                    veld_stats[vv.veld_naam]["ontbrekend"] += 1

        # Bereken accuratie per veld
        veld_stats_met_accuratie: dict[str, dict[str, int | float]] = {}
        for veld_naam, stats in veld_stats.items():
            vergelijkbare = stats["correct"] + stats["fout"]
            accuratie = (stats["correct"] / vergelijkbare * 100) if vergelijkbare > 0 else 0.0
            veld_stats_met_accuratie[veld_naam] = {
                "correct": stats["correct"],
                "fout": stats["fout"],
                "ontbrekend": stats["ontbrekend"],
                "accuratie_%": round(accuratie, 2),
            }

        return veld_stats_met_accuratie


# ==============================================================================
# Hulpfuncties
# ==============================================================================


def laad_gecachte_rak(rak_id: str) -> Rak | None:
    """Laad een gecachte Rak uit de cache directory.

    Parameters
    ----------
    rak_id : str
        RAK identifier (bijv. "HEG0201").

    Returns
    -------
    Rak | None
        Het geladen Rak object of None als niet gevonden.
    """
    # Zoek naar cache bestand dat de RAK ID bevat
    for cache_file in CACHE_DIR.glob(f"rak_*{rak_id}*.pkl"):
        try:
            with open(cache_file, "rb") as f:
                rak = pickle.load(f)
            if isinstance(rak, Rak):
                return rak
        except Exception as e:
            print(f"Fout bij laden van {cache_file}: {e}")
            continue

    return None


def haal_nested_attribuut_op(obj: Any, path: str) -> Any:
    """Haal een geneste attribuut waarde op via een dot-notated path.

    Parameters
    ----------
    obj : Any
        Het object waaruit de waarde gehaald moet worden.
    path : str
        Pad naar het attribuut (bijv. "bovenbouw.materiaal").

    Returns
    -------
    Any
        De waarde van het attribuut of None als niet gevonden.

    Examples
    --------
    >>> haal_nested_attribuut_op(rakdeel, "bovenbouw.materiaal")
    MateriaalBovenbouw.METSELWERK
    """
    delen = path.split(".")
    huidige = obj

    for deel in delen:
        if huidige is None:
            return None

        try:
            # Check of het een property of attribuut is
            huidige = getattr(huidige, deel)
        except AttributeError:
            return None

    return huidige


def waarden_zijn_gelijk(waarde1: Any, waarde2: Any, veld_type: type) -> bool:
    """Vergelijk twee waarden met type-awareness.

    Parameters
    ----------
    waarde1 : Any
        Eerste waarde (testset).
    waarde2 : Any
        Tweede waarde (parsing).
    veld_type : type
        Verwacht datatype voor type-specifieke vergelijking.

    Returns
    -------
    bool
        True als waarden als gelijk beschouwd worden.
    """
    # Beide None/NaN
    if pd.isna(waarde1) and pd.isna(waarde2):
        return True

    # Eén is None/NaN
    if pd.isna(waarde1) or pd.isna(waarde2):
        return False

    # Enum vergelijking: vergelijk op .value indien Enum
    try:
        from enum import Enum

        if isinstance(waarde1, Enum):
            waarde1 = waarde1.value if hasattr(waarde1, "value") else str(waarde1)
        if isinstance(waarde2, Enum):
            waarde2 = waarde2.value if hasattr(waarde2, "value") else str(waarde2)
    except Exception:
        pass

    # Boolean vergelijking
    if veld_type == bool:
        return bool(waarde1) == bool(waarde2)

    # Numerieke vergelijking met tolerantie
    if veld_type in (float, int) and isinstance(waarde1, (int, float)) and isinstance(waarde2, (int, float)):
        return abs(float(waarde1) - float(waarde2)) < 0.01

    # String vergelijking (case-insensitive)
    if veld_type == str:
        return str(waarde1).strip().lower() == str(waarde2).strip().lower()

    # Standaard vergelijking
    return waarde1 == waarde2


def vergelijk_rakdeel(
    testset_rij: pd.Series,
    rak: Rak,
    rakdeel_id: str,
    kolom_mappings: list[KolomMapping],
    testset_rakdeel_index: int | None = None,
    all_testset_rakdeel_ids: list[str] | None = None,
) -> RakdeelVergelijking | None:
    """Vergelijk één rakdeel uit testset met geparsed Rak object.

    Parameters
    ----------
    testset_rij : pd.Series
        Rij uit testset met verwachte waarden.
    rak : Rak
        Geparsed Rak object.
    rakdeel_id : str
        Rakdeel identifier om te vergelijken.
    kolom_mappings : list[KolomMapping]
        Lijst met kolom mappings om te vergelijken.

    Returns
    -------
    RakdeelVergelijking | None
        Vergelijkingsresultaat of None als rakdeel niet gevonden.
    """
    # Zoek het juiste rakdeel in het Rak object met meerdere heuristieken
    rakdeel = None

    # 1) Exact match (case-sensitive and case-insensitive)
    for rd in rak.rakdelen:
        if rd.rakdeel_id == rakdeel_id or str(rd.rakdeel_id).strip().lower() == str(rakdeel_id).strip().lower():
            rakdeel = rd
            break

    # 2) Suffix / letter match: testset vaak 'RAK-A' terwijl parsed is 'Constructie A'
    if rakdeel is None:
        # extract suffix after '-' or last token (e.g., 'KZG0202-A' -> 'A')
        m = re.search(r"-([A-Za-z0-9]+)$", str(rakdeel_id))
        suffix = m.group(1) if m else None
        if suffix:
            for rd in rak.rakdelen:
                rd_id = str(rd.rakdeel_id)
                # match ' A' or ending with the suffix
                if rd_id.strip().endswith(f" {suffix}") or rd_id.strip().endswith(suffix):
                    rakdeel = rd
                    break

    # 3) If still not found and counts match, fallback to index-based mapping
    if rakdeel is None and testset_rakdeel_index is not None and all_testset_rakdeel_ids is not None:
        try:
            testset_count = len(all_testset_rakdeel_ids)
            parsed_count = len(rak.rakdelen)
            if testset_count == parsed_count and 0 <= testset_rakdeel_index < parsed_count:
                rakdeel = rak.rakdelen[testset_rakdeel_index]
        except Exception:
            rakdeel = None

    if rakdeel is None:
        print(f"  Waarschuwing: Rakdeel {rakdeel_id} niet gevonden in geparsed Rak object")
        return None

    vergelijking = RakdeelVergelijking(rak_id=rak.raknaam, rakdeel_id=rakdeel_id)

    # Definitieve mapping van testset veld naar model property (uitbreidbaar)
    FIELD_PATH_MAP = {
        "bovenbouw.aantal_scheuren": "bovenbouw.totaal_aantal_scheuren",
        "bovenbouw.materiaal_bovenbouw": "bovenbouw.materiaal",
        "bovenbouw.maximale_scheurwijdte_mm": "bovenbouw.maximale_scheurwijdte_mm",
        "bovenbouw.percentage_niet_functionerend_schuifhout": "bovenbouw.percentage_niet_functionerend_schuifhout",
        "bovenbouw.is_lokaal_verdwenen_metselwerk": "bovenbouw.is_lokaal_verdwenen_metselwerk",
        "bovenbouw.is_grondvoerend_gat_aanwezig": "bovenbouw.is_grondvoerend_gat_aanwezig",
        "bovenbouw.is_buik_in_wand_aanwezig": "bovenbouw.is_buik_in_wand_aanwezig",
        "bovenbouw.is_scheur_t_p_v_buik_aanwezig": "bovenbouw.is_buik_met_scheur_aanwezig",
        "bovenbouw.is_scheefstand_aanwezig": "bovenbouw.is_scheefstand_aanwezig",
        "bovenbouw.scheur_bij_scheefstand_aanwezig": "bovenbouw.is_scheefstand_met_scheur_aanwezig",
        "onderbouw.percentage_slechte_palen": "onderbouw.percentage_slechte_palen",
        "onderbouw.percentage_ongewenste_schoorstand": "onderbouw.percentage_ongewenste_schoorstand",
        "onderbouw.percentage_beschadigde_kespen": "onderbouw.percentage_beschadigde_kespen",
        "onderbouw.percentage_beschadigde_verbinding": "onderbouw.percentage_beschadigde_verbinding",
        "onderbouw.vloer.materiaal": "onderbouw.vloer.materiaal",
        # Testset fields for materials map to `onderbouw.materiaal` on the model
        "onderbouw.materiaal_fundering": "onderbouw.materiaal_fundering",
        "onderbouw.materiaal_onderbouw": "onderbouw.materiaal",
        "onderbouw.vloer.is_beschadigd": "onderbouw.vloer.is_beschadigd",
        "onderbouw.onderloopsheidscherm.is_aanwezig": "onderbouw.onderloopsheidscherm",
        "onderbouw.onderloopsheidscherm.is_beschadigd": "onderbouw.onderloopsheidscherm.is_beschadigd",
        "vloer.bovenkant_vloer_cm_tov_nap": "onderbouw.vloer.bovenkant_vloer_cm_tov_nap",
        "lengte_rakdeel_m": "lengte_m",
        "rakdeel.bouwjaar": "bouwjaar",
        "rak.aantal_rakdelen": "rak.aantal_rakdelen",
    }

    # Vergelijk elk veld uit de mapping
    for mapping in kolom_mappings:
        veld_pad = mapping.datamodel_veld
        verwachte_waarde = testset_rij.get(veld_pad)

        # Translate to actual model path if present
        model_veld_pad = FIELD_PATH_MAP.get(veld_pad, veld_pad)

        # Bepaal basis object voor ophalen (rak of rakdeel)
        if model_veld_pad.startswith("rak."):
            basis_object = rak
            attribuut_pad = model_veld_pad[4:]
        elif model_veld_pad.startswith("rakdeel."):
            basis_object = rakdeel
            attribuut_pad = model_veld_pad[8:]
        else:
            basis_object = rakdeel
            attribuut_pad = model_veld_pad

        # Haal geparsede waarde op
        gekregen_waarde = haal_nested_attribuut_op(basis_object, attribuut_pad)

        # Als gekregen Enum is, gebruik value
        try:
            from enum import Enum

            if isinstance(gekregen_waarde, Enum):
                gekregen_waarde = gekregen_waarde.value if hasattr(gekregen_waarde, "value") else str(gekregen_waarde)
        except Exception:
            pass

        # Als het verwachte type bool is en de waarde een object is (geen scalair),
        # reduceer dan naar True/False op basis van aanwezigheid (niet-None = True)
        if (
            mapping.datatype == bool
            and gekregen_waarde is not None
            and not isinstance(gekregen_waarde, (bool, int, float, str))
        ):
            gekregen_waarde = True
        is_correct: bool | None = None
        verwacht_missing = pd.isna(verwachte_waarde) or verwachte_waarde is None
        gekregen_missing = gekregen_waarde is None or pd.isna(gekregen_waarde)

        if verwacht_missing and gekregen_missing:
            is_correct = None
        elif verwacht_missing or gekregen_missing:
            is_correct = None
        else:
            is_correct = waarden_zijn_gelijk(verwachte_waarde, gekregen_waarde, mapping.datatype)

        vergelijking.veld_vergelijkingen.append(
            VeldVergelijking(
                veld_naam=veld_pad, verwacht=verwachte_waarde, gekregen=gekregen_waarde, is_correct=is_correct
            )
        )

    return vergelijking


# ==============================================================================
# Excel export functies
# ==============================================================================


def exporteer_naar_excel(statistieken: VergelijkingsStatistieken, output_path: Path) -> None:
    """Exporteer vergelijkingsresultaten naar Excel met kleuren.

    Parameters
    ----------
    statistieken : VergelijkingsStatistieken
        Alle vergelijkingsresultaten en statistieken.
    output_path : Path
        Pad voor het output Excel bestand.
    """
    wb = Workbook()

    def safe_excel_value(val: Any) -> Any:
        """Convert values not supported by openpyxl to Excel-friendly types."""
        # pandas NA
        if pd.isna(val) or not val:
            return ""
        # Enums -> use their value or name
        try:
            from enum import Enum

            if isinstance(val, Enum):
                return val.value if hasattr(val, "value") else str(val)
        except Exception:
            pass

        # Complex types -> string representation
        if isinstance(val, (list, dict, tuple, set)):
            return str(val)

        return val

    # Sheet 1: Samenvatting per rakdeel
    ws_samenvatting = wb.active
    ws_samenvatting.title = "Samenvatting"

    samenvatting_data = []
    for rv in statistieken.rakdeel_vergelijkingen:
        samenvatting_data.append(
            {
                "rak_id": rv.rak_id,
                "rakdeel_id": rv.rakdeel_id,
                "totaal_velden": rv.totaal_velden,
                "correct": rv.aantal_correct,
                "fout": rv.aantal_fout,
                "ontbrekend": rv.aantal_ontbrekend,
                "accuratie_%": rv.accuratie_percentage,
            }
        )

    df_samenvatting = pd.DataFrame(samenvatting_data)
    for r_idx, row in enumerate(dataframe_to_rows(df_samenvatting, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            ws_samenvatting.cell(row=r_idx, column=c_idx, value=safe_excel_value(value))

    # Sheet 2: Gedetailleerde vergelijking
    ws_detail = wb.create_sheet("Gedetailleerde Vergelijking")

    detail_data = []
    for rv in statistieken.rakdeel_vergelijkingen:
        for vv in rv.veld_vergelijkingen:
            status = "ONTBREKEND" if vv.is_correct is None else ("CORRECT" if vv.is_correct else "FOUT")
            detail_data.append(
                {
                    "rak_id": rv.rak_id,
                    "rakdeel_id": rv.rakdeel_id,
                    "veld_naam": vv.veld_naam,
                    "verwacht": vv.verwacht,
                    "gekregen": vv.gekregen,
                    "status": status,
                }
            )

    df_detail = pd.DataFrame(detail_data)
    for r_idx, row in enumerate(dataframe_to_rows(df_detail, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws_detail.cell(row=r_idx, column=c_idx, value=safe_excel_value(value))

            # Kleur de status kolom (laatste kolom)
            if r_idx > 1 and c_idx == len(row):  # Skip header
                if value == "CORRECT":
                    cell.fill = KLEUR_CORRECT
                elif value == "FOUT":
                    cell.fill = KLEUR_FOUT
                elif value == "ONTBREKEND":
                    cell.fill = KLEUR_ONTBREEKT

    # Sheet 3: Matrix per rakdeel (breed formaat met kleuren per cel)
    ws_matrix = wb.create_sheet("Matrix per Rakdeel")

    # Bepaal alle unieke veld namen
    alle_velden = sorted(
        set(vv.veld_naam for rv in statistieken.rakdeel_vergelijkingen for vv in rv.veld_vergelijkingen)
    )

    # Header rij
    header = ["rak_id", "rakdeel_id"] + alle_velden
    for c_idx, veld in enumerate(header, 1):
        ws_matrix.cell(row=1, column=c_idx, value=veld)

    # Data rijen
    for r_idx, rv in enumerate(statistieken.rakdeel_vergelijkingen, 2):
        ws_matrix.cell(row=r_idx, column=1, value=rv.rak_id)
        ws_matrix.cell(row=r_idx, column=2, value=rv.rakdeel_id)

        # Maak dictionary voor snelle lookup
        veld_dict = {vv.veld_naam: vv for vv in rv.veld_vergelijkingen}

        for c_idx, veld_naam in enumerate(alle_velden, 3):
            if veld_naam in veld_dict:
                vv = veld_dict[veld_naam]
                cell = ws_matrix.cell(
                    row=r_idx, column=c_idx, value=str(vv.gekregen) if vv.gekregen is not None else ""
                )

                # Kleur de cel op basis van resultaat
                verwacht_missing = pd.isna(vv.verwacht) or vv.verwacht is None
                gekregen_missing = vv.gekregen is None or pd.isna(vv.gekregen)

                if verwacht_missing and gekregen_missing:
                    # Beide missing - wit (geen fill)
                    pass
                elif verwacht_missing or gekregen_missing:
                    # Eén missing - geel
                    cell.fill = KLEUR_ONTBREEKT
                elif vv.is_correct:
                    # Correct - groen
                    cell.fill = KLEUR_CORRECT
                else:
                    # Fout - rood
                    cell.fill = KLEUR_FOUT

    # Sheet 4: Statistieken per veld
    ws_veld_stats = wb.create_sheet("Statistieken per Veld")

    veld_stats = statistieken.statistieken_per_veld()
    veld_stats_data = []
    for veld_naam, stats in veld_stats.items():
        veld_stats_data.append({"veld_naam": veld_naam, **stats})

    df_veld_stats = pd.DataFrame(veld_stats_data)

    # Sorteer op accuratie (laagste eerst - meest problematisch) indien beschikbaar
    if not df_veld_stats.empty and "accuratie_%" in df_veld_stats.columns:
        df_veld_stats = df_veld_stats.sort_values("accuratie_%", ascending=True)

    if df_veld_stats.empty:
        ws_veld_stats.cell(row=1, column=1, value="Geen veldstatistieken beschikbaar")
    else:
        for r_idx, row in enumerate(dataframe_to_rows(df_veld_stats, index=False, header=True), 1):
            for c_idx, value in enumerate(row, 1):
                ws_veld_stats.cell(row=r_idx, column=c_idx, value=safe_excel_value(value))

    # Sla op
    wb.save(output_path)
    print(f"\nExcel geëxporteerd naar: {output_path}")


# ==============================================================================
# Main functie
# ==============================================================================


def main():
    """Hoofdfunctie voor vergelijking testset met parsing resultaten."""
    print("=" * 80)
    print("TESTSET VERGELIJKING MET PARSING RESULTATEN")
    print("=" * 80)

    # Laad testset
    testset_path = DATA_DIR / "ark" / "testset.xlsx"
    if not testset_path.exists():
        print(f"Fout: Testset niet gevonden: {testset_path}")
        return

    print(f"\nStap 1: Laden testset uit {testset_path.name}...")
    df_testset = pd.read_excel(testset_path, sheet_name="Testdata")
    print(f"  - {len(df_testset)} rakdelen gevonden in testset")

    # Groepeer per RAK ID
    unieke_rak_ids = df_testset["rak_id"].unique()
    print(f"  - {len(unieke_rak_ids)} unieke RAK IDs")

    statistieken = VergelijkingsStatistieken()

    print("\nStap 2: Vergelijken rakken...")
    for rak_id in unieke_rak_ids:
        print(f"\n  Verwerken: {rak_id}")

        # Laad gecachte Rak
        rak = laad_gecachte_rak(rak_id)
        if rak is None:
            print(f"    ⚠️  Geen gecachte Rak gevonden - overslaan")
            continue

        print(f"    ✓ Gecachte Rak geladen ({len(rak.rakdelen)} rakdelen)")

        # Filter testset rijen voor deze RAK
        testset_rijen = df_testset[df_testset["rak_id"] == rak_id]

        # Vergelijk elk rakdeel
        all_ids = list(testset_rijen["rakdeel_id"])
        for idx, (_, rij) in enumerate(testset_rijen.iterrows()):
            rakdeel_id = rij["rakdeel_id"]
            print(f"      - Vergelijken rakdeel: {rakdeel_id}")

            vergelijking = vergelijk_rakdeel(
                rij,
                rak,
                rakdeel_id,
                ARK_KOLOM_MAPPINGS,
                testset_rakdeel_index=idx,
                all_testset_rakdeel_ids=all_ids,
            )
            if vergelijking:
                statistieken.rakdeel_vergelijkingen.append(vergelijking)
                print(
                    f"        Resultaat: {vergelijking.aantal_correct} correct, "
                    f"{vergelijking.aantal_fout} fout, "
                    f"{vergelijking.aantal_ontbrekend} ontbrekend "
                    f"({vergelijking.accuratie_percentage}% accuratie)"
                )

    # Print samenvatting
    print("\n" + "=" * 80)
    print("SAMENVATTING STATISTIEKEN")
    print("=" * 80)
    print(f"Totaal rakdelen vergeleken: {statistieken.totaal_rakdelen}")
    print(f"Totaal velden vergeleken: {statistieken.totaal_velden}")
    print(f"  - Correct: {statistieken.totaal_correct}")
    print(f"  - Fout: {statistieken.totaal_fout}")
    print(f"  - Ontbrekend: {statistieken.totaal_ontbrekend}")
    print(f"Gemiddelde accuratie: {statistieken.gemiddelde_accuratie}%")

    # Top 5 slechtst presterende velden
    print("\n" + "-" * 80)
    print("TOP 5 VELDEN MET LAAGSTE ACCURATIE")
    print("-" * 80)
    veld_stats = statistieken.statistieken_per_veld()
    veld_stats_sorted = sorted(veld_stats.items(), key=lambda x: x[1]["accuratie_%"])[:5]
    for veld_naam, stats in veld_stats_sorted:
        print(
            f"  {veld_naam}: {stats['accuratie_%']}% "
            f"({stats['correct']} correct, {stats['fout']} fout, {stats['ontbrekend']} ontbrekend)"
        )

    # Exporteer naar Excel
    print("\nStap 3: Exporteren naar Excel...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = DATA_DIR / "ark" / f"testset_vergelijking_{timestamp}.xlsx"
    exporteer_naar_excel(statistieken, output_path)

    print("\n" + "=" * 80)
    print("KLAAR!")
    print("=" * 80)


if __name__ == "__main__":
    main()
