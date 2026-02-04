# RakBaseModel Automatic Type Hint Enhancement

## Overview

The `RakBaseModel` class now automatically adds `OnverwachtResultaat` as an alternative type to all non-collection attributes in its subclasses. This allows any field to gracefully handle unexpected or unparseable values.

## Implementation

The feature is implemented using Python's `__init_subclass__` hook, which is called automatically whenever a class inherits from `RakBaseModel`. The implementation:

1. Inspects all type annotations in the subclass
2. Identifies non-collection attributes (excludes `list`, `tuple`, `set`, `frozenset`, `dict`)
3. Automatically adds `| OnverwachtResultaat` to the type hint using `Union`
4. Preserves existing type hints for collection attributes

## Example

### Before
```python
class MyModel(RakBaseModel):
    naam: str
    leeftijd: int | None
    items: list[str]
```

### After (automatic transformation)
```python
class MyModel(RakBaseModel):
    naam: str | OnverwachtResultaat
    leeftijd: int | None | OnverwachtResultaat
    items: list[str]  # Collections remain unchanged
```

## Usage

### Normal values
```python
model = MyModel(
    naam="John",
    leeftijd=30,
    items=["a", "b"]
)
```

### With OnverwachtResultaat
```python
onverwacht = OnverwachtResultaat(
    waarde="parsing failed",
    onverwacht_resultaat_type=OnverwachtResultaatType.PARSING_FOUT,
    details="Could not extract name from document"
)

model = MyModel(
    naam=onverwacht,  # Instead of str, we pass OnverwachtResultaat
    leeftijd=30,
    items=["a", "b"]
)
```

## Benefits

1. **Type Safety**: Pydantic validation ensures that fields accept either the expected type or `OnverwachtResultaat`
2. **Error Handling**: Gracefully handle parsing errors without breaking the model
3. **Automatic**: No need to manually add `| OnverwachtResultaat` to every field
4. **Selective**: Only applies to non-collection fields
5. **Transparent**: Works seamlessly with existing code

## Detection

Models can detect unexpected results using the existing methods:
- `onverwachte_resultaten` property: Returns `OnverwachtResultaat` instances in the current model
- `alle_onverwachte_resultaten` property: Returns all `OnverwachtResultaat` instances in the model tree

## Testing

Comprehensive tests verify:
- Non-collection attributes get `OnverwachtResultaat` added
- Collection attributes remain unchanged
- Models can accept both normal values and `OnverwachtResultaat`
- Integration with Pydantic validation works correctly
