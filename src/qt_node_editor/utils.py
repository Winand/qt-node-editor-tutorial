import logging
import pkgutil
from pathlib import Path
from typing import Any, Generic, Type, TypeVar, cast

from qtpy.QtWidgets import QApplication

log = logging.getLogger(__name__)

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


def _load_stylesheet(filename: Path) -> str:
    if filename.is_file():
        stylesheet = filename.read_bytes()
    # Load file from package https://stackoverflow.com/a/58941536
    elif (stylesheet := pkgutil.get_data(__name__, str(filename))) is None:
        msg = f"Cannot load {filename}"
        raise FileNotFoundError(msg)
    return stylesheet.decode()


def load_stylesheet(filename: Path) -> None:
    """
    Apply stylesheet from file to application.

    File can be external or built-in in the package.
    """
    log.info("Style loading: %s", filename)
    cast(QApplication, QApplication.instance()) \
        .setStyleSheet(_load_stylesheet(filename))


def load_stylesheets(*filenames: Path) -> None:
    """
    Apply combined stylesheet from files to application.

    Files can be external or built-in in the package.
    """
    log.info("Style loading: %s", filenames)
    cast(QApplication, QApplication.instance()).setStyleSheet(
        "\n".join(map(_load_stylesheet, filenames)),
    )
