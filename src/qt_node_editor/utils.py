from typing import (Any, Generic, Type, TypeVar, cast)

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
