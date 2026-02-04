from __future__ import annotations
from pydantic import BaseModel

from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat


class RakBaseModel(BaseModel):
    """Base model for RAK related models."""

    gebreken: list[Gebrek] = []
    opmerkingen: str = ""

    @property
    def children(self) -> list[RakBaseModel]:
        """Return a list of child models that are a subclass of RakModelBase."""
        children = []
        for value in self.__dict__.values():
            if isinstance(value, RakBaseModel):
                children.append(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, RakBaseModel):
                        children.append(item)

        return children

    @property
    def alle_gebreken(self) -> list[Gebrek]:
        """Return a list of all Gebrek objects in this model and its children."""

        alle_gebreken = self.gebreken.copy()
        for child in self.children:
            alle_gebreken.extend(child.alle_gebreken)
        return alle_gebreken

    @property
    def onverwachte_resultaten(self) -> list[OnverwachtResultaat]:
        """Return a list of all OnverwachtResultaat objects in this model"""

        return [value for value in self.__dict__.values() if isinstance(value, OnverwachtResultaat)]

    @property
    def alle_onverwachte_resultaten(self) -> list[OnverwachtResultaat]:
        """Return a list of all OnverwachtResultaat objects in this model and its children."""

        alle_onverwachte_resultaten = self.onverwachte_resultaten.copy()
        for child in self.children:
            alle_onverwachte_resultaten.extend(child.alle_onverwachte_resultaten)
        return alle_onverwachte_resultaten
