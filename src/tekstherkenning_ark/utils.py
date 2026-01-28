import re
from azure.ai.documentintelligence.models import DocumentTable

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
    if value.strip().lower().startswith("nee"):
        return False

    try:
        return NietBeschikbaar(value.strip())
    except:
        pass

    raise ValueError(f"Invalid value for Ja/Nee parsing: `{value}`")


def contains_paal_id(value: str) -> bool:
    r"""Check if a string contains the pattern 'P\d.\d+' (e.g., P1.1, P2.10)"""

    pattern = r"P\d+\.\d+"
    return bool(re.search(pattern, value.strip()))


def contains_kesp_id(value: str) -> bool:
    r"""Check if a string contains the pattern 'K\d+' (e.g., K1, K24)"""

    pattern = r"K\d+"
    return bool(re.search(pattern, value.strip()))

def clean_string(value: str) -> str:
    """Clean an input string"""

    # Remove leading/trailing quotes
    cleaned_value = value.strip('"').strip("'").strip("`")

    # Remove anything between two ':' characters
    cleaned_value = re.sub(r":.*?:", "", cleaned_value)

    # Remove leading and trailing whitespace
    cleaned_value = cleaned_value.strip()

    return cleaned_value
