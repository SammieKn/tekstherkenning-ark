import re
import unicodedata
from azure.ai.documentintelligence.models import DocumentTable
from unidecode import unidecode

from tekstherkenning_ark.enums import NietBeschikbaar


def get_table_content(table: DocumentTable) -> list[list[str]]:
    """Get a table from the parsed_pdf as a pandas dataframe

    Parameters
    ----------
    table : DocumentTable
        The table to convert

    Returns
    -------
    list[list[str]]
        A list of lists of strings representing the table data
    """

    # Build table data
    table_data = [["" for _ in range(table.column_count)] for _ in range(table.row_count)]

    if table.cells:
        for cell in table.cells:
            row = cell.row_index
            col = cell.column_index
            if row < len(table_data) and col < len(table_data[0]):
                table_data[row][col] = cell.content if cell.content else ""

    return table_data


def parse_ja_nee(value: str) -> bool | NietBeschikbaar:
    """Parse a Ja/Nee string to a boolean value."""

    if value.strip().lower().startswith("ja"):
        return True
    if value.strip().lower().startswith("a"):
        return True  # Maar, geef melding dat dit niet standaard is - Matthias
    if value.strip().lower().startswith("nee"):
        return False

    try:
        return NietBeschikbaar(value.strip())
    except:
        pass

    raise ValueError(f"Invalid value for Ja/Nee parsing: `{value}`")


def clean_paal_id(value: str) -> str:
    """Correct for common errors in paal ID's.

    Known and accepted exceptions:
    - P.2.163
    - 21.169
    """

    value = clean_string(value)

    exceptions_dict = {
        "P.2.163": "P2.163",
        "21.169": "P2.169",
    }

    return exceptions_dict.get(value, value)


def contains_paal_id(value: str) -> bool:
    r"""Check if a string contains the pattern 'P\d.\d+' (e.g., P1.1, P2.10)"""

    pattern = r"P\d+\.\d+"
    return bool(re.search(pattern, value.strip()))


def contains_kesp_id(value: str) -> bool:
    r"""Check if a string contains the pattern 'K\d+' (e.g., K1, K24)"""

    pattern = r"K\d+"
    return bool(re.search(pattern, value.strip()))


def is_algemeen_gebrek(value: str) -> bool:
    """Check if a string indicates an 'algemeen gebrek'."""
    pattern = r"^GB\d{1,3}$"

    return bool(re.search(pattern, value.strip().upper())) or value == "Algemeen"


def is_houtmonster_id(value: str) -> bool:
    """Check if a string represents a valid houtmonsternummer codering,
    e.g. 'HEG0801/CONSTRUCTIE A/P1.16/HM'"""

    elements = clean_string(value).split("/")
    if len(elements) != 4:
        return False

    doc_id, constructie, paal_id, hm = elements

    if not "CONSTRUCTIE" in constructie or not contains_paal_id(paal_id) or not hm.lower().strip() == "hm":
        return False

    return True


def clean_string(value: str) -> str:
    """Clean an input string"""

    # Normalize unicode characters
    value = unidecode(value)

    # Remove leading/trailing quotes
    value = value.strip('"').strip("'").strip("`")

    # Remove anything between two ':' characters
    value = re.sub(r":.*?:", "", value)

    # Remove leading and trailing whitespace
    value = value.strip()

    return value
