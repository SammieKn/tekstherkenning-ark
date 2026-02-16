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
    ONDERLIGGENDE_DATA_INCORRECT = "onderliggende_data_incorrect"


class OnverwachtResultaat(BaseModel):
    """Dit model wordt gebruikt om onverwachte resultaten te representeren die kunnen optreden
    tijdens het verwerken van data, zoals parsing fouten, ontbrekende data, of data van een incorrect type.
    Het biedt een gestructureerde manier om deze situaties te loggen en af te handelen zonder dat het hele proces faalt.

    Speciaal gedrag: voor een `not` check (bijv. if not resultaat) zal een OnverwachtResultaat als False worden beschouwd net als None, lege string, etc.

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

    def __bool__(self):
        """Een OnverwachtResultaat wordt als False beschouwd in een boolean context, net als None, lege string, etc."""
        return False
