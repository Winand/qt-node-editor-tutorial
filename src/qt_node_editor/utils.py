from enum import Enum
from types import UnionType
from typing import (Any, Generic, Type, TypedDict, TypeVar, cast, get_args,
                    get_origin, is_typeddict)

T = TypeVar("T")
V = TypeVar("V")


def some(obj: T | None) -> T:
    "Casts an object to its type ignoring `None`."
    return cast(T, obj)


def As(var_type: Type[T]):
    "Cast object to a type using syntax: obj @As(Type)"
    # Note: Cannot use metaclass to define __rmatmul__ on type
    # https://github.com/python/mypy/issues/11672
    class _As(Generic[V]):
        @staticmethod
        def __rmatmul__(other: Any) -> V:
            return cast(V, other)
    return _As[var_type]()


# pylance returns T | Unknown, mypy - T | Any
class _Some():
    @staticmethod
    def __rmatmul__(other: T | None) -> T:
        if other is None:
            raise ValueError(f"Object {other} is None")
        return cast(T, other)

Some = _Some()


TD = TypeVar("TD", bound=TypedDict)

def _check_value(value, value_type):
    if isinstance(value_type, UnionType):
        for it in get_args(value_type):
            try:
                _check_value(value, it)
                break
            except TypeError:
                pass
        else:
            raise TypeError(f"{repr(value)} is not one of {value_type}")
    elif is_typeddict(value_type):
        validate_dict(value, value_type)
    elif issubclass(value_type, Enum):
        if value not in set(value_type):
            raise TypeError(f"{repr(value)} is not in {value_type} enum")
    elif not isinstance(value, value_type):
        raise TypeError(f"{repr(value)} is not {value_type}")

def validate_dict(data: dict, struct_type: type[TD]) -> TD:
    "Validate a dictionary."
    if not isinstance(data, dict):
        raise TypeError(f"{repr(data)} is not a {struct_type}")
    for key, value_type in struct_type.__annotations__.items():
        if key not in data:
            raise ValueError(f"Key '{key}' is missing")
        container_type = get_origin(value_type)
        if container_type == list:
            if not isinstance(data[key], container_type):
                raise TypeError(f"Key '{key}' is not a {container_type} container")
            for item in data[key]:
                sub_value_type = get_args(value_type)[0]
                _check_value(item, sub_value_type)
        else:
            _check_value(data[key], value_type)
    return cast(TD, data)
