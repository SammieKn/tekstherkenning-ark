"""
test fixtures for module tests

tests work only local -with data dir for now- what do we want?
"""

from functools import cache
import json
import pickle
import shutil
import socket
import pytest
from copy import deepcopy
from pathlib import Path

from tekstherkenning_ark.document.smart_document import SmartDocument
from tekstherkenning_ark.document.structured_table import StructuredTable
from tekstherkenning_ark.llm.azureopenaillm import AzureOpenAILLM
import pymupdf
from tekstherkenning_ark import constants
from pathlib import Path

from tekstherkenning_ark.models.onderbouw import Onderbouw
from tekstherkenning_ark.models.paal import Paal
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark.models.rakdeel import Rakdeel
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat
from tekstherkenning_ark.enums import AansluitingStatus


# Import mock data creators
from data.mock_rak_with_gebreken import create_mock_rak_with_gebreken
from data.mock_rak_with_onverwachte_resultaten import create_mock_rak_with_onverwachte_resultaten
from data.mock_rak_with_scheuren import create_mock_rak_with_scheuren
from data.mock_paal import MOCK_PAAL_RIJ_1_BASIS

# Test directory constants
TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / "data"

KZG_0202_DOC_NAME = "KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325"
KZG_0202_PKL_NAME = f"{KZG_0202_DOC_NAME}_smart_document_lokaal.pkl"
KZG_0202_TEST_DIR = TEST_DATA_DIR / "KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325"

def pytest_addoption(parser: pytest.Parser) -> None:
    """Registreer de optionele lokale corpuscontrole.

    Parameters
    ----------
    parser : pytest.Parser
        Pytest-commandoregelparser.
    """
    parser.addoption("--pdf-corpus", action="store_true", help="Controleer alle lokale duikrapporten zonder cloudcalls.")


@pytest.fixture(scope="session", autouse=True)
def isoleer_testcache(tmp_path_factory: pytest.TempPathFactory):
    """Kopieer gecachte LLM-antwoorden; schrijf nooit in de referentiefixtures.

    Parameters
    ----------
    tmp_path_factory : pytest.TempPathFactory
        Maakt een tijdelijke cache voor de hele testsessie.

    Yields
    ------
    Path
        Tijdelijke cache met uitsluitend bestaande classificatieantwoorden.
    """
    cache_map = tmp_path_factory.mktemp("llm_cache")
    for bestand in KZG_0202_TEST_DIR.glob("*.pkl"):
        if not bestand.name.startswith("rak_") and "_smart_document_" not in bestand.name:
            shutil.copyfile(bestand, cache_map / bestand.name)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(constants, "CACHE_DIR", cache_map)
        yield cache_map


@pytest.fixture(scope="session", autouse=True)
def verbied_externe_diensten():
    """Laat ontbrekende fixtures hard falen in plaats van OCR of betaalde calls te starten.

    Yields
    ------
    None
        Actieve netwerk-, OCR- en Azure OpenAI-blokkade.
    """
    def verboden_aanroep(*args, **kwargs):
        """Meld een verboden externe bewerking tijdens een offline test."""
        pytest.fail("OCR/netwerk/echte LLM-verwerking is verboden; gebruik een fixture of mock.", pytrace=False)

    originele_connect = socket.socket.connect

    def controleer_connect(verbinding: socket.socket, adres):
        """Sta alleen interne loopbacksockets voor de Windows-eventloop toe.

        Parameters
        ----------
        verbinding : socket.socket
            Te verbinden socket.
        adres : tuple | str
            Bestemming; uitsluitend lokale loopback is toegestaan.
        """
        if isinstance(adres, tuple) and adres[0] in {"127.0.0.1", "::1"}:
            return originele_connect(verbinding, adres)
        verboden_aanroep()

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(socket.socket, "connect", controleer_connect)
        patch.setattr(socket, "create_connection", verboden_aanroep)
        patch.setattr(pymupdf.Page, "get_textpage_ocr", verboden_aanroep)
        patch.setattr(AzureOpenAILLM, "__init__", verboden_aanroep)
        yield


@cache
def load_kzg0202_smart_document() -> SmartDocument:
    """Lees de gemigreerde eigen fixture zonder SDK-import of nieuwe extractie.

    Returns
    -------
    SmartDocument
        Eigen documenttypen met dezelfde historische domeininvoer.
    """

    return pickle.loads((KZG_0202_TEST_DIR / KZG_0202_PKL_NAME).read_bytes())


@pytest.fixture(scope="session")
def kzg0202_smart_document() -> SmartDocument:
    """Geef de vertrouwde SDK-vrije documentfixture.

    Returns
    -------
    SmartDocument
        Historische referentiedata in eigen documenttypen.
    """
    return load_kzg0202_smart_document()


@pytest.fixture(scope="session")
def kzg0202_rak(isoleer_testcache: Path, verbied_externe_diensten) -> Rak:

    smart_doc = load_kzg0202_smart_document()

    # rak
    rak = Rak.from_smart_document(smart_doc, use_caching=False)  # use cached LLM parts but not rak itself
    return rak


@pytest.fixture(scope="session")
def paal_tables() -> StructuredTable:
    """Fixture to provide a complete mock Rak object with gebreken at various levels."""
    loaded_doc = load_kzg0202_smart_document()

    paal_tables = loaded_doc.get_meettabel_fundering_paal()

    return paal_tables


@pytest.fixture()
def mock_rak_with_gebreken() -> Rak:
    """Fixture to provide a complete mock Rak object with gebreken at various levels."""

    return create_mock_rak_with_gebreken()


@pytest.fixture()
def mock_rak_with_onverwachte_resultaten() -> Rak:
    """Fixture to provide a complete mock Rak object with OnverwachtResultaat at various levels."""

    return create_mock_rak_with_onverwachte_resultaten()


@pytest.fixture()
def mock_rak_with_scheuren() -> Rak:
    """Fixture to provide a mock Rak object for testing scheur calculations."""

    return create_mock_rak_with_scheuren()


@pytest.fixture()
def mock_rakdeel(mock_rak_with_gebreken: Rak) -> Rakdeel:
    """Fixture to provide a single Rakdeel from the mock Rak with gebreken."""
    return mock_rak_with_gebreken.rakdelen[0]


@pytest.fixture()
def mock_onderbouw(mock_rakdeel: Rakdeel) -> Onderbouw:
    """Fixture to provide the Onderbouw from the mock Rakdeel with gebreken."""
    return mock_rakdeel.onderbouw


@pytest.fixture()
def mock_rakdeel_with_scheuren(mock_rak_with_scheuren: Rak) -> Rakdeel:
    """Fixture to provide a single Rakdeel for testing maximaal_aantal_scheuren_per_10_m."""
    return mock_rak_with_scheuren.rakdelen[0]


@pytest.fixture()
def mock_palen(mock_rak_with_gebreken: Rak) -> list[Paal]:
    """Fixture to provide a list of Palen from the first Rakdeel of the mock Rak with gebreken."""
    return mock_rak_with_gebreken.rakdelen[0].onderbouw.palen


@pytest.fixture()
def mock_rak_with_scheuren_json() -> str:
    """Fixture to provide a JSON string of a mock Rak with scheuren for testing JSON serialization."""

    mock_rak_with_scheuren_json_path = TEST_DATA_DIR / "mock_rak_with_scheuren.json"
    return mock_rak_with_scheuren_json_path.read_text()


@pytest.fixture()
def maak_paal_rij_1():
    """Maak een standaard paal in rij 1 met overschreven paalnummer en aansluitingsstatus.

    Returns
    -------
    Callable
        Functie die een ``Paal`` opbouwt uit vaste mock data en opgegeven overrides.
    """

    def maak(paal_nummer: str, aansluiting_status: AansluitingStatus | OnverwachtResultaat) -> Paal:
        paal_data = deepcopy(MOCK_PAAL_RIJ_1_BASIS)
        paal_data["paal_nummer"] = paal_nummer
        paal_data["aansluiting_status"] = aansluiting_status
        return Paal(**paal_data)

    return maak
