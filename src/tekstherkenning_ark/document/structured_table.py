from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from azure.ai.documentintelligence.models import DocumentTable

from tekstherkenning_ark.logger import get_logger
from tekstherkenning_ark.utils import (
    clean_string,
    get_kesp_id,
    get_paal_id,
    get_table_content,
    is_table_type_by_id_func,
    remove_invalid_rows,
    remove_titel_rows,
)

logger = get_logger(__name__)


@dataclass(frozen=True)
class StructuredTable:
    """A structured representation of a table extracted from a document, with methods to access its values based on headers, sub-headers and units.
    Used for parsing the palen, kespen and houtmonsters tables in the rakdeel secties.

    The dataclass is frozen, meaning the structured table should not be modified after creation.
    Some functions are cached for performance reasons thus the underlying data should be immutable to avoid issues."""

    columns: list[TableColumn]
    table_type: Literal["palen", "kespen", "houtmonsters"]

    col_lookup_cache: dict[tuple, TableColumn] = field(default_factory=dict, init=False, repr=False)

    @property
    def num_rows(self) -> int:
        return len(self.columns[0].values) if self.columns else 0

    @classmethod
    def from_doc_table(
        cls, tables: list[DocumentTable], table_type: Literal["palen", "kespen", "houtmonsters"]
    ) -> StructuredTable:
        """Parse and return a StructuredTable object from table rows.

        Parameters
        ----------
        table_rows : list[list[str]]
            List of table rows as lists of strings.

        Returns
        -------
        StructuredTable
            A StructuredTable object containing information from the table with headers, sub-headers, units, and values.
        """

        # Validate table type
        if not table_type in ["palen", "kespen", "houtmonsters"]:
            raise ValueError(f"Invalid table type: {table_type}. Expected 'palen', 'kespen' or 'houtmonsters'.")

        id_func_dict = {"palen": get_paal_id, "kespen": get_kesp_id, "houtmonsters": None}
        id_func = id_func_dict[table_type]

        # Extract rows from all tables
        rows: list[list[str]] = []
        for tabel in tables:
            if id_func is None or is_table_type_by_id_func(tabel, id_func):
                rows.extend(get_table_content(tabel))
        rows_wo_header = remove_titel_rows(rows)
        table_rows = remove_invalid_rows(rows_wo_header)

        # Determine if the table has a sub-header row based on the table type
        has_sub_header = table_type in ["palen", "kespen"]
        sub_header_col_offset = int(has_sub_header)

        # If there is no data or there are no value rows, return an empty StructuredTable
        if len(table_rows) <= (2 + sub_header_col_offset):
            return StructuredTable(columns=[], table_type=table_type)

        # Transpose rows to columns
        columns = list(zip(*table_rows))

        # Create TableColumn objects for each column
        table_columns = TableColumn.from_column_lists(columns, has_sub_header=has_sub_header)

        return StructuredTable(columns=table_columns, table_type=table_type)

    def get_value(
        self,
        header_in: str | list[str] = "",
        sub_header_in: str | list[str] = "",
        unit_in: str | list[str] = "",
        index: int = 0,
    ) -> str | None:
        """Get a value from the structured table based on header, sub-header, unit and row index by matching against possible values. Matching is case-insensitive."""

        column = self.get_column(header_in, sub_header_in, unit_in)
        if not column is None and column.values:
            return clean_string(column.values[index])

        return None

    def get_column(
        self,
        header_in: str | list[str] = "",
        sub_header_in: str | list[str] = "",
        unit_in: str | list[str] = "",
    ) -> TableColumn | None:
        """Get a column from the structured table based on header, sub-header and unit by matching against possible values.
        Matching is case-insensitive.

        Unit is only considered if there are multiple matches based on header and sub-header.

        Parameters
        ----------
        header_in : str | list[str], optional
            List of possible header values to match. If not provided the header is ignored.
        sub_header_in : str | list[str], optional
            List of possible sub-header values to match. If not provided the sub-header is ignored.
        unit_in : str | list[str], optional
            List of possible unit values to match. If not provided the unit is ignored.

        Returns
        -------
        TableColumn | None
            The matching TableColumn object or None if no match is found.
        """

        # Convert single string inputs to lists for uniform processing
        if isinstance(header_in, str):
            header_in = [header_in]
        if isinstance(sub_header_in, str):
            sub_header_in = [sub_header_in]
        if isinstance(unit_in, str):
            unit_in = [unit_in]

        # Check cache first (for performance reasons)
        cache_key = (tuple(header_in), tuple(sub_header_in), tuple(unit_in))
        if cache_key in self.col_lookup_cache:
            return self.col_lookup_cache[cache_key]

        # Make everything lowercase for case-insensitive matching
        header_in = [h.lower() for h in header_in] if header_in else None
        sub_header_in = [sh.lower() for sh in sub_header_in] if sub_header_in else None
        unit_in = [u.lower() for u in unit_in] if unit_in else None

        # Determine columns that match header and sub-header criteria
        header_matching_columns = [c for c in self.columns if not header_in or c.header.lower() in header_in]
        subheader_matching_columns = [
            c for c in header_matching_columns if not sub_header_in or c.sub_header.lower() in sub_header_in
        ]

        # If exactly one column matches based on header and sub-header, return it.
        if len(subheader_matching_columns) == 1:
            self.col_lookup_cache[cache_key] = subheader_matching_columns[0]
            return subheader_matching_columns[0]

        # If multiple columns match based on header and sub-header, use unit to disambiguate if possible.
        elif len(subheader_matching_columns) > 1 and unit_in is not None:
            for column in subheader_matching_columns:
                if column.unit.lower() in unit_in:
                    self.col_lookup_cache[cache_key] = column
                    return column

        # No matching columns, warn
        available_subheaders_str = ""
        if header_matching_columns:
            available_subheaders = sorted([c.sub_header for c in header_matching_columns if c.sub_header])
            if available_subheaders:
                available_subheaders_str = (
                    "Available sub-headers within header: " + ", ".join(available_subheaders) + ". "
                )
        logger.warning(
            f"No matching column found for {self.table_type} table for arguments {header_in}, {sub_header_in}, {unit_in}. {available_subheaders_str}Returning None."
        )
        self.col_lookup_cache[cache_key] = None
        return None


@dataclass
class TableColumn:
    header: str
    sub_header: str = ""
    unit: str = ""
    values: list[str] = None

    @classmethod
    def from_column_lists(cls, columns: list[list[str]], has_sub_header: bool) -> list[TableColumn]:
        """Create TableColumn objects from lists of column values, determining headers, sub-headers and units based on the table type.

        Parameters
        ----------
        columns : list[list[str]]
            List of columns as lists of strings, where the first few rows may contain headers, sub-headers and units.
        has_sub_header : bool
            Indicates whether the table has a sub-header row (e.g. for palen and kespen tables).

        Returns
        -------
        list[TableColumn]
            A list of TableColumn objects containing header, sub-header, unit and values for each column.
        """

        sub_header_col_offset = int(has_sub_header)
        header_i = int(not has_sub_header)  # 0 if we have a sub-header, 1 if we don't

        # Create TableColumn objects for each column
        table_columns = []
        last_header_value = ""
        last_sub_header_value = ""
        last_unit_value = ""

        for col in columns:
            if col[header_i]:
                last_header_value = col[header_i]
                last_sub_header_value = ""
                last_unit_value = ""

            if has_sub_header and col[1]:
                last_sub_header_value = col[1]
                last_unit_value = ""

            last_unit_value = col[1 + sub_header_col_offset] or last_unit_value
            values = list(col[2 + sub_header_col_offset :])

            table_columns.append(cls(last_header_value, last_sub_header_value, last_unit_value, values))

        return table_columns
