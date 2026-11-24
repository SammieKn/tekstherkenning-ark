from __future__ import annotations

from typing import Annotated, Any, Self, Type, TypeVar, Union, cast, get_args, get_origin

import pandas as pd
from pydantic import BaseModel, ValidationError
from pydantic.functional_validators import WrapValidator
from pydantic_core.core_schema import ValidationInfo

from tekstherkenning_ark import utils
from tekstherkenning_ark.enums import NietBeschikbaar
from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat
from tekstherkenning_ark.models.toestand_onderdeel import ToestandOnderdeel

T = TypeVar("T", Gebrek, OnverwachtResultaat, ToestandOnderdeel)

gebrek_classes = tuple([Gebrek] + Gebrek.__subclasses__())
T_Gebrek = TypeVar("T_Gebrek", bound=Union[gebrek_classes])


def validate_with_onverwacht_fallback(value: Any, handler, info: ValidationInfo) -> Any:
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
            details=f"Validation error for attribute {info.field_name }: {str(e)}",
        )


class RakBaseModel(BaseModel):
    """Base model for RAK related models."""

    # We add all gebrek subtypes here for proper json serialization of gebrek subclasses
    gebreken: list[T_Gebrek] = []
    opmerkingen: str = ""
    toestand_onderdelen: list[ToestandOnderdeel] = []

    @classmethod
    def _models_from_nomic_df(cls, frame: pd.DataFrame, fields: tuple[str, ...]) -> list[Self]:
        """Create model instances from matching columns in a Nomic dataframe.

        Parameters
        ----------
        frame : pandas.DataFrame
            Rows containing the source model data.
        fields : tuple[str, ...]
            Model fields to read from the dataframe columns.

        Returns
        -------
        list[Self]
            One instance per dataframe row.
        """
        return [cls(**cls.nomic_model_values(row, fields)) for row in frame.to_dict(orient="records")]

    @staticmethod
    def _require_nomic_columns(frame: pd.DataFrame, columns: tuple[str, ...]) -> None:
        """Raise a clear error if required Nomic columns are missing."""
        missing_columns = set(columns) - set(frame.columns)
        if missing_columns:
            raise ValueError(f"Nomic dataframe is missing required columns: {', '.join(sorted(missing_columns))}")

    @staticmethod
    def _nomic_text(value: Any) -> str:
        """Normalize an identifier or text value from a Nomic dataframe."""
        if value is None or bool(pd.isna(value)):
            return ""
        return str(value).strip()

    @classmethod
    def nomic_model_values(cls, row: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
        """Extract and normalize model fields from a Nomic CSV row.

        Parameters
        ----------
        row : dict[str, Any]
            A row whose keys are Nomic column names.
        fields : tuple[str, ...]
            Model fields to extract.

        Returns
        -------
        dict[str, Any]
            Normalized values ready for model construction.
        """
        values = {}
        for field in fields:
            value = row.get(field)
            if value is None or (isinstance(value, str) and not value.strip()) or bool(pd.isna(value)):
                annotation = cls.model_fields[field].annotation
                if cls._annotation_contains(annotation, type(None)):
                    value = None
                elif cls._annotation_contains(annotation, str):
                    value = ""
                elif cls._annotation_contains(annotation, NietBeschikbaar):
                    value = NietBeschikbaar.LEEG
                else:
                    value = None
            elif cls._annotation_contains(cls.model_fields[field].annotation, bool):
                value = cls._parse_nomic_bool(value)
            values[field] = value
        return values

    @staticmethod
    def _annotation_contains(annotation: Any, expected_type: type) -> bool:
        """Return whether an annotation contains a type within its arguments."""
        return annotation is expected_type or any(
            RakBaseModel._annotation_contains(argument, expected_type) for argument in get_args(annotation)
        )

    @staticmethod
    def _parse_nomic_bool(value: Any) -> bool | NietBeschikbaar | OnverwachtResultaat:
        """Parse common boolean values from Nomic exports."""
        if isinstance(value, bool) or isinstance(value, NietBeschikbaar):
            return value
        text = str(value).strip().lower()
        if text in {"true", "ja", "yes", "1"}:
            return True
        if text in {"false", "nee", "no", "0"}:
            return False
        return utils.parse_ja_nee(text)

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

        values = list(self.__dict__.values())
        computed_values = [
            getattr(self, attr)
            for attr in self.__class__.model_computed_fields
            if not "onverwachte_resultaten" in attr
        ]

        return [value for value in values + computed_values if isinstance(value, OnverwachtResultaat)]

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
        elif obj_type == ToestandOnderdeel:
            obj_list = self.toestand_onderdelen
        else:
            raise ValueError(f"obj_type should be either `Gebrek` or `OnverwachtResultaat`, not '{obj_type}'")
        result = [(current_path, gebrek) for gebrek in obj_list]

        # Recursively collect from children
        for child in self.children:
            result.extend(child._get_all_with_path(obj_type=obj_type, prefix=current_path))

        return cast(list[tuple[str, T]], result)

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

    @property
    def alle_toestandsbepalingen(self) -> list[tuple[str, ToestandOnderdeel]]:
        """Return a list of tuples (path, toestand_onderdeel) for all ToestandOnderdeel objects in this model and its children.

        The path is a slash-separated string of identifiers showing the hierarchy,
        e.g., 'raknaam/rakdeel_id/onderbouw/vloer'.
        """
        return self._get_all_with_path(obj_type=ToestandOnderdeel)
