"""
Module defining the UnexpectedResult for handling unexpected results in the tekstherkenning_ark package.
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, model_validator
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
