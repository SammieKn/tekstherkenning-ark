from __future__ import annotations
from typing import Type, TypeVar, get_args, get_origin, Union, Annotated, Any, Union
from pydantic import BaseModel, ValidationError
from pydantic.functional_validators import WrapValidator

from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat

T = TypeVar("T", Gebrek, OnverwachtResultaat)


def validate_with_onverwacht_fallback(value: Any, handler, info) -> Any:
    """Validator that wraps values in OnverwachtResultaat if validation fails."""
    # If already an OnverwachtResultaat, return it
    if isinstance(value, OnverwachtResultaat):
        return value

    # Try normal validation
    try:
        return handler(value)
    except ValidationError as e:
        # If validation fails, wrap in OnverwachtResultaat
        from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaatType

        return OnverwachtResultaat(
            waarde=value,
            onverwacht_resultaat_type=OnverwachtResultaatType.INCORRECT_TYPE,
            details=f"Validation error: {str(e)}",
        )


class RakBaseModel(BaseModel):
    """Base model for RAK related models."""

    gebreken: list[Gebrek] = []
    opmerkingen: str = ""
    toestand_onderdelen: dict[str, bool | NietBeschikbaar | OnverwachtResultaat] = {}

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

                # If not a collection, add OnverwachtResultaat as a union type with validator
                if not is_collection:
                    # Check if OnverwachtResultaat is already in the type
                    if get_origin(attr_type) is Union:
                        args = get_args(attr_type)
                        if OnverwachtResultaat not in args:
                            # Add as Annotated with wrap validator
                            new_annotations[attr_name] = Annotated[
                                Union[attr_type, OnverwachtResultaat], WrapValidator(validate_with_onverwacht_fallback)
                            ]
                        else:
                            new_annotations[attr_name] = attr_type
                    else:
                        # Add OnverwachtResultaat to the type with wrap validator
                        new_annotations[attr_name] = Annotated[
                            Union[attr_type, OnverwachtResultaat], WrapValidator(validate_with_onverwacht_fallback)
                        ]
                else:
                    new_annotations[attr_name] = attr_type

            cls.__annotations__ = new_annotations

    @property
    def onverwachte_resultaten(self) -> list[OnverwachtResultaat]:
        """Return a list of all OnverwachtResultaat objects in this model"""

        return [value for value in self.__dict__.values() if isinstance(value, OnverwachtResultaat)]

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

    def _get_all_with_path(self, obj_type: Type[T], prefix: str = "") -> list[tuple[str, T]]:
        """Helper method to recursively collect gebreken with their identifier paths.

        Args:
            prefix: The parent path prefix to prepend to this object's identifier.

        Returns:
            List of tuples containing (full_path, gebrek) for all gebreken in this model and its children.
        """
        current_path = f"{prefix}/{self.identifier}" if prefix else self.identifier

        # Add objects from this model
        if obj_type == Gebrek:
            obj_list = self.gebreken
        elif obj_type == OnverwachtResultaat:
            obj_list = self.onverwachte_resultaten
        else:
            raise ValueError(f"obj_type should be either `Gebrek` or `OnverwachtResultaat`, not '{obj_type}'")
        result = [(current_path, gebrek) for gebrek in obj_list]

        # Recursively collect from children
        for child in self.children:
            result.extend(child._get_all_with_path(obj_type=obj_type, prefix=current_path))

        return result

    @property
    def alle_onverwachte_resultaten(self) -> list[tuple[str, OnverwachtResultaat]]:
        """Return a list of tuples (path, onverwacht_resultaat) for all OnverwachtResultaat objects.

        The path is a slash-separated string of identifiers showing the hierarchy,
        e.g., 'raknaam/rakdeel_id/bovenbouw/metselwerk'.
        """
        return self._get_all_with_path(obj_type=OnverwachtResultaat)

    @property
    def alle_gebreken(self) -> list[tuple[str, Gebrek]]:
        """Return a list of tuples (path, gebrek) for all Gebrek objects in this model and its children.

        The path is a slash-separated string of identifiers showing the hierarchy,
        e.g., 'raknaam/rakdeel_id/onderbouw/paal_nummer'.
        """
        return self._get_all_with_path(obj_type=Gebrek)
