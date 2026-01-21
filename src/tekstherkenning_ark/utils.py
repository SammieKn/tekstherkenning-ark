from azure.ai.documentintelligence.models import DocumentTable


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
