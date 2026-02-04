from __future__ import annotations
from typing import get_args, get_origin, Union
from pydantic import BaseModel

from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat


class RakBaseModel(BaseModel):
    """Base model for RAK related models."""

    gebreken: list[Gebrek] = []
    opmerkingen: str = ""

    @property
    def identifier(self) -> str:
        """Return a string that uniquely identifies this model instance."""
        raise NotImplementedError("Subclasses must implement the identifier property.")

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

    def _get_alle_gebreken_with_path(self, prefix: str = "") -> list[tuple[str, Gebrek]]:
        """Helper method to recursively collect gebreken with their identifier paths.
        
        Args:
            prefix: The parent path prefix to prepend to this object's identifier.
            
        Returns:
            List of tuples containing (full_path, gebrek) for all gebreken in this model and its children.
        """
        current_path = f"{prefix}.{self.identifier}" if prefix else self.identifier
        
        # Add gebreken from this model
        result = [(current_path, gebrek) for gebrek in self.gebreken]
        
        # Recursively collect from children
        for child in self.children:
            result.extend(child._get_alle_gebreken_with_path(current_path))
        
        return result

    @property
    def alle_gebreken(self) -> list[tuple[str, Gebrek]]:
        """Return a list of tuples (path, gebrek) for all Gebrek objects in this model and its children.
        
        The path is a dot-separated string of identifiers showing the hierarchy,
        e.g., 'raknaam.rakdeel_id.onderbouw.paal_nummer'.
        """
        return self._get_alle_gebreken_with_path()

    @property
    def onverwachte_resultaten(self) -> list[OnverwachtResultaat]:
        """Return a list of all OnverwachtResultaat objects in this model"""

        return [value for value in self.__dict__.values() if isinstance(value, OnverwachtResultaat)]

    def _get_alle_onverwachte_resultaten_with_path(self, prefix: str = "") -> list[tuple[str, OnverwachtResultaat]]:
        """Helper method to recursively collect onverwachte resultaten with their identifier paths.
        
        Args:
            prefix: The parent path prefix to prepend to this object's identifier.
            
        Returns:
            List of tuples containing (full_path, onverwacht_resultaat) for all onverwachte resultaten.
        """
        current_path = f"{prefix}.{self.identifier}" if prefix else self.identifier
        
        # Add onverwachte resultaten from this model
        result = [(current_path, onverwacht) for onverwacht in self.onverwachte_resultaten]
        
        # Recursively collect from children
        for child in self.children:
            result.extend(child._get_alle_onverwachte_resultaten_with_path(current_path))
        
        return result

    @property
    def alle_onverwachte_resultaten(self) -> list[tuple[str, OnverwachtResultaat]]:
        """Return a list of tuples (path, onverwacht_resultaat) for all OnverwachtResultaat objects.
        
        The path is a dot-separated string of identifiers showing the hierarchy,
        e.g., 'raknaam.rakdeel_id.bovenbouw.metselwerk'.
        """
        return self._get_alle_onverwachte_resultaten_with_path()
