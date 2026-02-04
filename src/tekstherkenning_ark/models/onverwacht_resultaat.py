"""
Module defining the UnexpectedResult for handling unexpected results in the tekstherkenning_ark package.
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, ValidationError, model_validator
from pydantic_core import core_schema
from typing import Any as AnyType
from tekstherkenning_ark.logger import get_logger

logger = get_logger(__name__)


# OnverwachtResultaat types
class OnverwachtResultaatType(Enum):
    """OnverwachtResultaatType enumeration."""

    EXCEPTIE = "exceptie"
    INCORRECT_TYPE = "incorrect_type"
    PARSING_FOUT = "parsing_fout"
    ONBEKEND = "onbekend"


class OnverwachtResultaat(BaseModel):
    """OnverwachtResultaat.

    Parameters
    -----------
    waarde: Any
        De (onverwachte) waarde die is gevonden.
    onverwacht_resultaat_type: OnverwachtResultaatType
        Het type van het onverwachte resultaat.
    details: str
        Eventuele aanvullende details over het onverwachte resultaat.

    """

    waarde: Any
    onverwacht_resultaat_type: OnverwachtResultaatType = OnverwachtResultaatType.ONBEKEND
    details: str = ""

    @model_validator(mode="after")
    def log_unexpected_result(self):
        """Log a warning whenever an OnverwachtResultaat is created."""
        logger.debug(
            f"OnverwachtResultaat created - Type: {self.onverwacht_resultaat_type.value}, "
            f"Value: {self.waarde}, Details: {self.details}"
        )
        return self

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: AnyType, handler):
        """Define custom Pydantic validation schema that catches validation errors."""
        python_schema = handler(source_type)

        def validate_with_fallback(value, handler):
            """Wrap validator that catches validation errors for union types."""
            # If it's already an OnverwachtResultaat, return it
            if isinstance(value, OnverwachtResultaat):
                return value

            # Try to validate with the original schema
            try:
                return handler(value)
            except ValidationError as e:
                # If validation fails, wrap in OnverwachtResultaat
                return OnverwachtResultaat(
                    waarde=value,
                    onverwacht_resultaat_type=OnverwachtResultaatType.INCORRECT_TYPE,
                    details=f"Validation error: {str(e)}",
                )

        return core_schema.no_info_wrap_validator_function(
            validate_with_fallback,
            python_schema,
        )
