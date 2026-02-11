from __future__ import annotations

from functools import cache
import re
from azure.ai.documentintelligence.models import DocumentTable
from unidecode import unidecode

from tekstherkenning_ark.enums import NietBeschikbaar

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat

# Regex patterns for ID extraction and validation
PAAL_ID_PATTERN = r"\bP\d+\.\d+\b"
KESP_ID_PATTERN = r"\bK\d+\b"
RAK_ID_PATTERN = r"([A-Z]{3}\d{4})(-\d{2})?"
CONSTRUCTIE_PATTERN = r"constructie [a-z]"
ALGEMEEN_GEBREK_PATTERN = r"^GB\d{1,3}$"


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


def parse_ja_nee(value: str) -> bool | NietBeschikbaar | OnverwachtResultaat:
    """Parse a Ja/Nee string to a boolean value."""
    from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat, OnverwachtResultaatType

    if value is None:
        return None

    if value.strip().lower().startswith("ja"):
        return True
    if value.strip().lower().startswith("a"):
        return True  # Maar, geef melding dat dit niet standaard is - Matthias
    if value.strip().lower().startswith("nee"):
        return False

    try:
        return NietBeschikbaar(value.strip())
    except:
        return OnverwachtResultaat(
            waarde=value,
            onverwacht_resultaat_type=OnverwachtResultaatType.PARSING_FOUT,
            details=f"Kan Ja/Nee waarde niet parsen o.b.v. : `{value}`",
        )


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

    value = clean_paal_id(clean_string(value))

    return bool(re.search(PAAL_ID_PATTERN, value.strip()))


def contains_kesp_id(value: str) -> bool:
    r"""Check if a string contains the pattern 'K\d+' (e.g., K1, K24)"""

    return bool(re.search(KESP_ID_PATTERN, value.strip()))


def get_paal_id(value: str) -> str | None:
    r"""Extract paal ID from a string (e.g., P1.1, P2.10, P2.163).

    Parameters
    ----------
    value : str
        Input string that may contain a paal ID

    Returns
    -------
    str | None
        The extracted paal ID or None if not found
    """
    value = clean_paal_id(clean_string(value))

    match = re.search(PAAL_ID_PATTERN, value.strip())

    return match.group(0) if match else None


def get_kesp_id(value: str) -> str | None:
    r"""Extract kesp ID from a string (e.g., K1, K24).

    Parameters
    ----------
    value : str
        Input string that may contain a kesp ID

    Returns
    -------
    str | None
        The extracted kesp ID or None if not found
    """
    value = clean_string(value)

    match = re.search(KESP_ID_PATTERN, value.strip())

    return match.group(0) if match else None


def get_rak_id(value: str) -> str | None:
    r"""Extract rak ID from a string (e.g., ABC1234, DEF5678-01).

    Parameters
    ----------
    value : str
        Input string that may contain a rak ID

    Returns
    -------
    str | None
        The extracted rak ID or None if not found
    """
    value = clean_string(value)

    match = re.search(RAK_ID_PATTERN, value.strip())

    return match.group(0) if match else None


def get_constructienaam(value: str) -> str | None:
    r"""Extract constructie naam from a string (e.g., 'Constructie A', 'constructie b').

    Parameters
    ----------
    value : str
        Input string that may contain a constructie naam

    Returns
    -------
    str | None
        The extracted constructie naam or None if not found
    """
    value = clean_string(value)

    match = re.search(CONSTRUCTIE_PATTERN, value.lower())
    if match:
        naam = match.group(0)
        if len(naam) > 1:
            naam = naam[0].upper() + naam[1:-1] + naam[-1].upper()
        else:
            naam = naam.upper()
        return naam
    return None


def is_algemeen_gebrek(value: str) -> bool:
    """Check if a string indicates an 'algemeen gebrek'."""

    return bool(re.search(ALGEMEEN_GEBREK_PATTERN, value.strip().upper())) or value == "Algemeen"


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


def remove_titel_rows(
    table_rows: list[list[str]], titel_keywords: list[str] = ["Titel", "Rapportnummer"]
) -> list[list[str]]:
    """Remove rows from a table that contain any of the specified titel keywords."""

    return [
        row
        for row in table_rows
        if not any(keyword.lower() in cell.lower() for cell in row for keyword in titel_keywords)
    ]


def remove_invalid_rows(table_rows: list[list[str]]) -> list[list[str]]:
    if not table_rows:
        return table_rows

    max_kolommen = max(len(row) for row in table_rows)

    return [row for row in table_rows if len(row) == max_kolommen]


@cache
def clean_string(value: str) -> str:
    """Clean an input string"""

    # Normalize unicode characters
    value = unidecode(value)

    # Remove leading/trailing quotes
    value = value.strip().strip('"').strip("'").strip("`")

    # Remove anything between two ':' characters
    value = re.sub(r":.*?:", "", value)

    # Remove leading and trailing whitespace
    value = value.strip()

    return value


def is_table_type_by_id_func(
    tabel: DocumentTable, id_func: Callable[[str], str | None], threshold: float = 0.5
) -> bool:
    """Check of een tabel bij een type hoort op basis van een ID-extractie functie.

    Parameters
    ----------
    tabel : DocumentTable
        De tabel om te controleren.
    id_func : callable
        Functie die een string neemt en een ID of None teruggeeft (bijv. get_paal_id).
    threshold : float
        Minimale fractie van cellen die moeten matchen.

    Returns
    -------
    bool
        True als de tabel voldoet aan het type.
    """
    if not tabel.cells:
        return False

    first_col_cells = [cell.content for cell in tabel.cells if cell.column_index == 0]
    if not first_col_cells:
        return False

    matching_cells = sum(1 for cell in first_col_cells if id_func(cell) is not None)
    return (matching_cells / len(first_col_cells)) > threshold
