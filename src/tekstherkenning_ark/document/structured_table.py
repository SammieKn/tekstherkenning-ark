from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from functools import cached_property
import math
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


class TableType(StrEnum):
    PALEN = "palen"
    KESPEN = "kespen"
    HOUTMONSTERS = "houtmonsters"
    GEBREKEN = "gebreken"
    TOESTANDSBEPALING = "toestandsbepaling"

    @cached_property
    def has_sub_header(self) -> bool:
        """Only palen and kespen have a sub-header row."""

        return self in [self.PALEN, self.KESPEN]

    @cached_property
    def has_unit(self) -> bool:
        """Only palen, kespen and houtmonsters have a unit row."""

        return self in [self.PALEN, self.KESPEN, self.HOUTMONSTERS]

    @cached_property
    def unit_offset(self) -> int:
        """Return the expected row index for the unit row based on the table type."""

        return int(self.has_sub_header) + int(self.has_unit)

    @cached_property
    def values_offset(self) -> int:
        """Calculate the offset for the first row of values based on the presence of header, sub-header and unit rows."""

        return self.unit_offset + 1

    @cached_property
    def expected_header_colnames(self) -> list[str]:
        """Return expected header column names for this table type in lowercase for case-insensitive matching."""

        if self is self.PALEN:
            return [
                "paalnummer",
                "diameter",
                "hart-op-hart-afstanden",
                "schoorstand",
                "afstand",
                "schades",
                "aansluiting",
                "opmerkingen",
                "onderzocht",
            ]
        elif self is self.KESPEN:
            return [
                "kespnummer",
                "afmetingen",
                "hoek t.o.v. lengte-as frontwand",
                "lengte uitstekende deel t.o.v. voorzijde frontwand",
                "mate van inknijping",
                "indrukking van de funderingspaal in de kesp",
                "opsluitklos",
                "schades",
            ]
        elif self is self.HOUTMONSTERS:
            return [
                "codering",
                "rakcode",
                "paalnummer",
                "houtmonster",
                "diameter paal",
                "hoogte t.o.v. nap",
                "hoogte t.o.v. kesp/vloer",
                "wankant aanwezig?",
                "datum monstername",
            ]
        elif self is self.GEBREKEN:
            return [
                "gebrekcodering",
                "omschrijving",
                "figuurnummer",
            ]
        elif self is self.TOESTANDSBEPALING:
            return [
                "constructieonderdeel",
                "aangetast",
            ]
        else:
            raise NotImplementedError(f"Expected header column names not defined for table type: {self}")


@dataclass(frozen=True)
class StructuredTable:
    """A structured representation of a table extracted from a document, with methods to access its values based on headers, sub-headers and units.
    Used for parsing the palen, kespen, houtmonsters, gebreken and toestandsbepaling tables in the rakdeel secties.

    The dataclass is frozen, meaning the structured table should not be modified after creation.
    Some functions are cached for performance reasons thus the underlying data should be immutable to avoid issues."""

    columns: list[TableColumn]
    table_type: TableType

    col_lookup_cache: dict[tuple, TableColumn] = field(default_factory=dict, init=False, repr=False)

    @property
    def num_rows(self) -> int:
        return len(self.columns[0].values) if self.columns else 0

    @classmethod
    def from_doc_table(
        cls,
        tables: list[DocumentTable],
        table_type: TableType,
    ) -> StructuredTable | None:
        """Parse and return a StructuredTable object from table rows.

        Parameters
        ----------
        tables: list[DocumentTable]
            List of DocumentTable objects to parse and find the relevant table based on the table type.
        table_type: TableType
            The type of the table to parse, which determines how headers, sub-headers and units are identified and how the values are extracted.
            Possible values: "palen", "kespen", "houtmonsters", "gebreken", "toestandsbepaling".

        Returns
        -------
        StructuredTable
            A StructuredTable object containing information from the table with headers, sub-headers, units, and values.
        """

        # Ensure table_type is a valid TableType enum member
        table_type = TableType(table_type)

        # Define a mapping of table types to their corresponding ID extraction functions (if applicable)
        id_func_dict = {
            TableType.PALEN: get_paal_id,
            TableType.KESPEN: get_kesp_id,
        }

        id_func = id_func_dict.get(table_type, None)

        # Extract rows from all tables
        rows: list[list[str]] = []
        for tabel in tables:
            if id_func is None or is_table_type_by_id_func(tabel, id_func):
                rows.extend(get_table_content(tabel))
        rows_wo_header = remove_titel_rows(rows)
        valid_table_rows = remove_invalid_rows(rows_wo_header)

        table_rows = cls.remove_rows_before_header(valid_table_rows, table_type)

        # If there is no data or there are no value rows, return an empty StructuredTable
        if not table_rows or len(table_rows) <= table_type.values_offset:
            return None

        # Transpose rows to columns
        columns = list(zip(*table_rows))

        # Create TableColumn objects for each column
        table_columns = TableColumn.from_column_lists(columns, table_type)

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
        if column is not None and column.values:
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

        if not self.columns:
            return None

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

    @staticmethod
    def is_header_row(row: list[str], table_type: TableType, threshold: float = 0.5) -> bool:
        """Return whether the current row is likely to be a header row or not"""

        row_clean = [clean_string(val).lower() for val in row]
        row_values = [val for val in row_clean if val]

        present_count = sum(val in table_type.expected_header_colnames for val in row_values)
        required_count = int(math.ceil(len(row_values) * threshold))
        return present_count >= required_count

    @classmethod
    def remove_rows_before_header(cls, table_rows: list[list[str]], table_type: TableType) -> list[list[str]]:
        """Remove rows before the header row based on the expected header column names for the given table type."""

        if not table_rows:
            return table_rows

        # Get the header row location
        first_header_row_index = next(
            (index for index, row in enumerate(table_rows) if cls.is_header_row(row, table_type)), None
        )

        # Return the table rows starting from the header row (inclusive) or the original rows if no header row is found
        # Filter out all the additional header rows after the first one
        if first_header_row_index is not None:
            return [
                row
                for i, row in enumerate(table_rows[first_header_row_index:])
                if i == 0 or not cls.is_header_row(row, table_type)
            ]

        logger.warning(f"No header row found for table type {table_type}. Returning original rows.")
        return table_rows


@dataclass
class TableColumn:
    header: str
    sub_header: str = ""
    unit: str = ""
    values: list[str] = None

    @classmethod
    def from_column_lists(
        cls,
        columns: list[list[str]],
        table_type: TableType,
    ) -> list[TableColumn]:
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

        # Create TableColumn objects for each column
        table_columns = []
        last_header_value = ""
        last_sub_header_value = ""
        last_unit_value = ""

        for col in columns:
            if col[0]:
                last_header_value = col[0]
                last_sub_header_value = ""
                last_unit_value = ""

            if table_type.has_sub_header and col[1]:
                last_sub_header_value = col[1]
                last_unit_value = ""

            if table_type.has_unit and col[table_type.unit_offset]:
                last_unit_value = col[table_type.unit_offset]

            values = list(col[table_type.values_offset :])

            table_columns.append(cls(last_header_value, last_sub_header_value, last_unit_value, values))

        return table_columns
