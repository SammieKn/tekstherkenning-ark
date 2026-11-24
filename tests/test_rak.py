"""
We willen de volgende "integratietesten" uitvoeren voor de Rak klasse:

- gegeven goed geparste SmartDocument een rak object zonder OnverwachtResultaat
- gegeven geparste SmartDocument met enkele gebreken een rak object met OnverwachtResultaat in veld X
- gegeven een onvolledig SmartDocument (ontbreken van tabellen en of teksten) een rak object met OnverwachtResultaat in veld Y

TODO:
 - gegeven kzg0202 hoeveel OnverwachtResultaat in totaal willen/verwachten we echt?

Uitgangspunten:
We testen NIET het LLM classificatieproces zelf.
We halen de smart doc en LLM resultaten uit de fixtures,
zodat we de testdata kunnen controleren en aanpassen indien nodig.

"""

import csv
import json
from pathlib import Path

import pytest
from polyfactory.factories.pydantic_factory import ModelFactory

from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.houtmonster import Houtmonster
from tekstherkenning_ark.models.rak import Rak


def _write_nomic_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    """Write a small Nomic CSV fixture."""
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _create_nomic_csv_fixture(
    csv_dir: Path,
    include_houtmonsters: bool = False,
    onderloopsheidscherm: str | None = None,
) -> None:
    """Create the required CSV tables for one rak and one rakdeel."""
    _write_nomic_csv(
        csv_dir / "rakken.csv",
        ("raknaam", "totale_lengte_m", "opmerkingen"),
        [{"raknaam": "TESTRAK", "totale_lengte_m": "12.5", "opmerkingen": "Raknotitie"}],
    )
    _write_nomic_csv(
        csv_dir / "rakdelen.csv",
        ("rak_id", "rakdeel_id", "omschrijving", "lengte_m_omschrijving", "bouwjaar", "opmerkingen"),
        [
            {
                "rak_id": "TESTRAK",
                "rakdeel_id": "Constructie A",
                "omschrijving": "Betonnen constructie.",
                "lengte_m_omschrijving": "12.5",
                "bouwjaar": "1998",
                "opmerkingen": "Rakdeelnotitie",
            }
        ],
    )
    _write_nomic_csv(
        csv_dir / "bovenbouw.csv",
        ("rak_id", "rakdeel_id", "materiaal", "bovenkant_deksteen_cm_tov_nap", "opmerkingen"),
        [
            {
                "rak_id": "TESTRAK",
                "rakdeel_id": "Constructie A",
                "materiaal": "Metselwerk",
                "bovenkant_deksteen_cm_tov_nap": "1.5",
                "opmerkingen": "Bovenbouwnotitie",
            }
        ],
    )
    onderbouw_columns = ("rak_id", "rakdeel_id", "materiaal", "materiaal_fundering", "opmerkingen")
    onderbouw_row = {
        "rak_id": "TESTRAK",
        "rakdeel_id": "Constructie A",
        "materiaal": "Hout",
        "materiaal_fundering": "Hout",
        "opmerkingen": "Onderbouwnotitie",
    }
    if onderloopsheidscherm is not None:
        onderbouw_columns += ("onderloopsheidscherm",)
        onderbouw_row["onderloopsheidscherm"] = onderloopsheidscherm
    _write_nomic_csv(csv_dir / "onderbouw.csv", onderbouw_columns, [onderbouw_row])
    _write_nomic_csv(
        csv_dir / "palen.csv",
        (
            "rak_id",
            "rakdeel_id",
            "paal_nummer",
            "diameter_haaks",
            "diameter_parallel",
            "diameter_gemiddeld",
            "hoh_afstand_cm",
            "hoh_paalnummer",
            "schoor_graden",
            "schoor_richting",
            "afstand_frontwand_cm",
            "is_scheefstand",
            "is_paalbreuk",
            "is_aantasting",
            "aansluiting_status",
            "positionering_aansluiting_cm",
            "opmerkingen",
        ),
        [
            {
                "rak_id": "TESTRAK",
                "rakdeel_id": "Constructie A",
                "paal_nummer": "P1.1",
                "diameter_haaks": "200",
                "diameter_parallel": "210",
                "diameter_gemiddeld": "205",
                "hoh_afstand_cm": "50",
                "hoh_paalnummer": "P1.2",
                "schoor_graden": "0",
                "schoor_richting": "LR",
                "afstand_frontwand_cm": "10",
                "is_scheefstand": "False",
                "is_paalbreuk": "False",
                "is_aantasting": "False",
                "aansluiting_status": "G",
                "positionering_aansluiting_cm": "0",
                "opmerkingen": "Paalnotitie",
            }
        ],
    )
    _write_nomic_csv(
        csv_dir / "kespen.csv",
        (
            "rak_id",
            "rakdeel_id",
            "kesp_nummer",
            "hoogte_cm",
            "breedte_cm",
            "hoek_tov_lengte_as_graden",
            "lengte_uitstekend_deel_cm",
            "mate_inknijping_cm",
            "indrukking_paal_in_kesp",
            "is_opsluitklos_aanwezig",
            "is_opsluitklos_aangetast",
            "is_vervormd",
            "is_aangetast",
            "opmerkingen",
        ),
        [
            {
                "rak_id": "TESTRAK",
                "rakdeel_id": "Constructie A",
                "kesp_nummer": "K1",
                "hoogte_cm": "20",
                "breedte_cm": "25",
                "hoek_tov_lengte_as_graden": "0",
                "lengte_uitstekend_deel_cm": "30",
                "mate_inknijping_cm": "0",
                "indrukking_paal_in_kesp": "False",
                "is_opsluitklos_aanwezig": "True",
                "is_opsluitklos_aangetast": "False",
                "is_vervormd": "False",
                "is_aangetast": "False",
                "opmerkingen": "Kespnotitie",
            }
        ],
    )
    _write_nomic_csv(
        csv_dir / "gebreken.csv",
        ("rak_id", "rakdeel_id", "model_pad", "codering", "omschrijving", "figuurnummer"),
        [
            {
                "rak_id": "TESTRAK",
                "rakdeel_id": "Constructie A",
                "model_pad": "bovenbouw",
                "codering": "GB1",
                "omschrijving": "Een generiek gebrek.",
                "figuurnummer": "",
            },
            {
                "rak_id": "TESTRAK",
                "rakdeel_id": "Constructie A",
                "model_pad": "onderbouw/palen",
                "codering": "TESTRAK/P1.1/GB",
                "omschrijving": "Een generiek paalgebrek.",
                "figuurnummer": "",
            },
        ],
    )
    _write_nomic_csv(
        csv_dir / "toestandsbepalingen.csv",
        ("rak_id", "rakdeel_id", "model_pad", "onderdeel", "aangetast"),
        [
            {
                "rak_id": "TESTRAK",
                "rakdeel_id": "Constructie A",
                "model_pad": "bovenbouw",
                "onderdeel": "bovenbouw",
                "aangetast": "Ja",
            },
            {
                "rak_id": "TESTRAK",
                "rakdeel_id": "Constructie A",
                "model_pad": "onderbouw/vloer",
                "onderdeel": "vloer",
                "aangetast": "Nee",
            },
        ],
    )
    if include_houtmonsters:
        _write_nomic_csv(
            csv_dir / "houtmonsters.csv",
            (
                "rak_id",
                "rakdeel_id",
                "codering",
                "rak_code",
                "paal_nummer",
                "houtmonster_code",
                "diameter_paal_ter_hoogte_houtmonster_mm",
                "hoogte_onder_nap_cm",
                "hoogte_tov_onderzijde_fundering_cm",
                "is_wankant_aanwezig",
                "datum_monstername",
                "is_aangetast",
                "stichtingjaar",
                "opmerkingen",
            ),
            [
                {
                    "rak_id": "TESTRAK",
                    "rakdeel_id": "Constructie A",
                    "codering": "TESTRAK/P1.1/HM",
                    "rak_code": "TESTRAK",
                    "paal_nummer": "P1.1",
                    "houtmonster_code": "HM00001",
                    "diameter_paal_ter_hoogte_houtmonster_mm": "205",
                    "hoogte_onder_nap_cm": "140",
                    "hoogte_tov_onderzijde_fundering_cm": "20",
                    "is_wankant_aanwezig": "True",
                    "datum_monstername": "30-03-2022",
                    "is_aangetast": "False",
                    "stichtingjaar": "1900",
                    "opmerkingen": "Monster notitie",
                }
            ],
        )


def test_from_nomic_csvs_builds_rak_hierarchy_and_generic_defects(tmp_path: Path):
    """Load nested data while leaving unavailable attributes unset and defects generic."""
    _create_nomic_csv_fixture(tmp_path)

    rak = Rak.from_nomic_csvs(tmp_path)
    rakdeel = rak.rakdelen[0]

    assert rak.raknaam == "TESTRAK"
    assert rak.totale_lengte_m == 12.5
    assert rak.opmerkingen == "Raknotitie"
    assert rakdeel.rakdeel_id == "Constructie A"
    assert rakdeel.onderbouw.palen[0].paal_nummer == "P1.1"
    assert rakdeel.onderbouw.palen[0].gebreken[0].codering == "TESTRAK/P1.1/GB"
    assert rakdeel.onderbouw.kespen[0].kesp_nummer == "K1"
    assert rakdeel.bovenbouw.gebreken[0].__class__ is Gebrek
    assert rakdeel.bovenbouw.toestand_onderdelen[0].aangetast is True
    assert rakdeel.onderbouw.vloer is not None
    assert rakdeel.onderbouw.vloer.materiaal == NietBeschikbaar.LEEG
    assert rakdeel.onderbouw.vloer.bovenkant_vloer_cm_tov_nap is None
    assert rakdeel.onderbouw.vloer.is_meerdere_locaties is None
    assert rakdeel.onderbouw.onderloopsheidscherm is not None
    assert rakdeel.onderbouw.onderloopsheidscherm.is_meerdere_locaties is None
    assert rak.unassigned_houtmonsters == []


def test_from_nomic_csvs_assigns_houtmonsters_to_paal(tmp_path: Path):
    """Load HEG-style wood-sample columns and attach each sample to its pile."""
    _create_nomic_csv_fixture(tmp_path, include_houtmonsters=True)

    rak = Rak.from_nomic_csvs(tmp_path)
    houtmonster = rak.rakdelen[0].onderbouw.palen[0].houtmonsters[0]

    assert isinstance(houtmonster, Houtmonster)
    assert houtmonster.houtmonster_code == "HM00001"
    assert houtmonster.diameter_paal_ter_hoogte_houtmonster_mm == 205
    assert houtmonster.stichtingjaar == 1900
    assert rak.unassigned_houtmonsters == []


def test_from_nomic_csvs_honors_explicit_missing_screen_flag(tmp_path: Path):
    """Keep the screen absent when the optional CSV flag explicitly says false."""
    _create_nomic_csv_fixture(tmp_path, onderloopsheidscherm="False")

    rak = Rak.from_nomic_csvs(tmp_path)

    assert rak.rakdelen[0].onderbouw.onderloopsheidscherm is None


def test_from_nomic_csvs_requires_non_optional_csv_files(tmp_path: Path):
    """Raise an explicit error when a required Nomic CSV is missing."""
    _create_nomic_csv_fixture(tmp_path)
    (tmp_path / "kespen.csv").unlink()

    with pytest.raises(FileNotFoundError, match="kespen.csv"):
        Rak.from_nomic_csvs(tmp_path)


def test_kzg0202(kzg0202_rak: Rak):
    """Test that the fixture loads a Rak instance from the test cache correctly."""
    assert isinstance(kzg0202_rak, Rak)
    assert len(kzg0202_rak.rakdelen) == 10, f"Expected 10 rakdelen, got {len(kzg0202_rak.rakdelen)}"


def test_kzg0202_nul_onverwacht(kzg0202_rak: Rak):
    """Test that the Rak instance from the test cache has the expected gebreken."""
    resultaten = kzg0202_rak.rakdelen[0].alle_onverwachte_resultaten
    aantal_overwacht_tot = len(resultaten)
    assert aantal_overwacht_tot == 0, f"Expected 0 onverwachte resultaten, got {aantal_overwacht_tot}"


def test_kzg0202_gebreken(kzg0202_rak: Rak):
    """Test that the Rak instance from the test cache has the expected gebreken."""
    aantal_gebreken_tot = len(kzg0202_rak.alle_gebreken)
    assert aantal_gebreken_tot == 79, f"Expected 79 gebreken, got {aantal_gebreken_tot}"
    # header gebrekcodering constructie B tabel meegneomen als onbekend gebrek


def test_kzg0202_raknaam(kzg0202_rak: Rak):
    """Test that the Rak instance from the test cache has the expected raknaam."""
    raknaam = kzg0202_rak.raknaam
    assert raknaam == "KZG0202", f"Expected raknaam 'KZG0202', got '{raknaam}'"


def test_kzg0202_aantallen(kzg0202_rak: Rak):
    """Test that the Rak instance from the test cache has the expected aantallen."""
    rak = kzg0202_rak
    assert len(rak.alle_palen) == 139, f"Expected 139 palen, got {len(rak.alle_palen)}"
    assert len(rak.alle_houtmonsters) == 52, f"Expected 52 houtmonstersn, got {len(rak.alle_houtmonsters)}"
    assert (
        len(rak.alle_kespen) == 97
    ), f"Expected 97 kespen, got {len(rak.alle_kespen)}"  # Kesp8,  80 and 84 missing maybe


def test_kzg0202_kesp_breedtes(kzg0202_rak: Rak):
    """
    test kesp breedtes
    """
    all_hoogtes = []
    all_non_numeric = []
    for _, kesp in kzg0202_rak.alle_kespen:
        if isinstance(kesp.hoogte_cm, int):
            all_hoogtes.append(kesp.hoogte_cm)
        else:
            all_non_numeric.append(kesp.hoogte_cm)
    assert (
        len(all_non_numeric) == 1
    ), f"Expected 1 non-numeric kesp hoogte, got {len(all_non_numeric)}: {all_non_numeric}"
    assert sum(all_hoogtes) == 1549, f"Expected total height of 1550 cm, got {sum(all_hoogtes)}"
    # expected = 1549 + 1"NM" (total len 97, numerical len 96)


class TestRakToJson:
    def test_mock_rak_scheuren_to_json(self, mock_rak_with_scheuren: Rak, mock_rak_with_scheuren_json: str):
        """Test that a mock Rak with scheuren can be serialized to JSON."""
        json_str = mock_rak_with_scheuren.model_dump_json(indent=2)

        # Uncomment these line to update the expected JSON file with the current output
        # (useful when intentionally changing the model structure or test data)

        # from tests.conftest import TEST_DATA_DIR
        # (TEST_DATA_DIR / "mock_rak_with_scheuren.json").write_text(json_str, encoding="utf-8")

        expected_dict = json.loads(mock_rak_with_scheuren_json)
        actual_dict = json.loads(json_str)

        assert (
            actual_dict["rakdelen"][0]["bovenbouw"]["gebreken"]
            == expected_dict["rakdelen"][0]["bovenbouw"]["gebreken"]
        ), "Gebreken in bovenbouw komen niet overeen"

        assert actual_dict["rakdelen"][0]["alle_gebreken"] == expected_dict["rakdelen"][0]["alle_gebreken"]

    @pytest.mark.parametrize("gebrek_class", [Gebrek] + Gebrek.__subclasses__())
    def test_gebrek_subclasses_to_json(self, gebrek_class: type[Gebrek]):
        """Test that all Gebrek subclasses can be serialized to JSON."""

        # Create a mock instance of the subclass using a ModelFactory,
        # which will fill in all required fields with dummy data
        class SubclassMockFactory(ModelFactory[gebrek_class]):
            __model__ = gebrek_class

        instance = SubclassMockFactory.build()

        # Check if we actually got an instance of the correct class
        assert isinstance(instance, gebrek_class), f"Factory did not create an instance of {gebrek_class.__name__}"

        # Put the gebrek in a Rak
        rak = Rak(
            raknaam="TESTRAK",
            totale_lengte_m=10.0,
            rakdelen=[],
            gebreken=[instance],
        )

        # Create the JSON string from the instance
        json_str = rak.model_dump_json(indent=2)

        assert json_str is not None, f"JSON serialization failed for {gebrek_class.__name__}"

        # Retrieve all expected fields for the subclass
        expected_fields = list(gebrek_class.model_fields.keys()) + list(gebrek_class.model_computed_fields.keys())

        # Subclasses should have more fields than the base Gebrek class
        if gebrek_class != Gebrek:
            assert len(expected_fields) > len(Gebrek.model_fields) + len(Gebrek.model_computed_fields)

        # Check if all expected fields are present in the JSON output
        for field in expected_fields:
            assert (
                f'"{field}":' in json_str
            ), f"Expected field '{field}' not found in JSON output for {gebrek_class.__name__}"
