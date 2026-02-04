from __future__ import annotations
from typing import get_args, get_origin, Union
from pydantic import BaseModel

from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat


class RakBaseModel(BaseModel):
    """Base model for RAK related models."""

    gebreken: list[Gebrek] = []
    opmerkingen: str = ""

    def __init_subclass__(cls, **kwargs):
        """Automatically add OnverwachtResultaat to non-collection attributes in subclasses."""
        super().__init_subclass__(**kwargs)

        # Get annotations from this class only (not inherited)
        if hasattr(cls, "__annotations__"):
            new_annotations = {}
            for attr_name, attr_type in cls.__annotations__.items():
                # Check if the attribute is a collection type
                origin = get_origin(attr_type)
                is_collection = origin in (list, tuple, set, frozenset, dict)

                # If not a collection, add OnverwachtResultaat as a union type
                if not is_collection:
                    # Check if OnverwachtResultaat is already in the type
                    if get_origin(attr_type) is Union:
                        args = get_args(attr_type)
                        if OnverwachtResultaat not in args:
                            new_annotations[attr_name] = Union[attr_type, OnverwachtResultaat]
                        else:
                            new_annotations[attr_name] = attr_type
                    else:
                        # Add OnverwachtResultaat to the type
                        new_annotations[attr_name] = Union[attr_type, OnverwachtResultaat]
                else:
                    new_annotations[attr_name] = attr_type

            cls.__annotations__ = new_annotations

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
