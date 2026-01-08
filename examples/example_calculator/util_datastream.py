from enum import IntEnum
from typing import Any

from qtpy.QtCore import QByteArray, QDataStream, QIODevice
from qtpy.QtGui import QPixmap

type QtSerializable = bool | int | float | str | bytes | QPixmap


def to_bytearray(*args: QtSerializable) -> QByteArray:
    """
    Serialize multiple values into a QByteArray using QDataStream.

    Supported types:
    - int, float, bool, str, bytes
    - QPixmap

    Returns:
        QByteArray: Serialized data

    """
    byte_array = QByteArray()
    stream = QDataStream(byte_array, QIODevice.OpenModeFlag.WriteOnly)
    for arg in args:
        if isinstance(arg, bool):
            stream.writeBool(arg)
        elif isinstance(arg, int):
            stream.writeInt32(arg)
        elif isinstance(arg, float):
            stream.writeDouble(arg)
        elif isinstance(arg, str):
            stream.writeQString(arg)
        elif isinstance(arg, bytes):
            stream.writeBytes(arg)
        elif isinstance(arg, (QPixmap,)):
            stream << arg  # pyright: ignore[reportUnusedExpression, reportOperatorIssue]
        else:
            msg = f"Unsupported type for serialization: {type(arg)}"
            raise TypeError(msg)
    return byte_array


def from_bytearray(byte_array: QByteArray, *types: type[QtSerializable],
                   ) -> tuple[Any, ...]:
    """
    Deserialize values from a QByteArray using QDataStream.

    Args:
        byte_array: QByteArray containing serialized data
        *types: Type objects indicating what to read (int, float, str, bytes, bool, QPixmap)

    Returns:
        tuple: Deserialized values

    """
    def _read_value(stream: QDataStream, typ: type[QtSerializable]) -> QtSerializable:
        if issubclass(typ, bool):
            return stream.readBool()
        if issubclass(typ, int):
            v = stream.readInt32()
            return typ(v) if issubclass(typ, IntEnum) else v
        if issubclass(typ, float):
            return stream.readDouble()
        if issubclass(typ, str):
            return stream.readQString()
        if issubclass(typ, bytes):
            return stream.readBytes()
        if issubclass(typ, QPixmap):
            obj = typ()
            stream >> obj  # pyright: ignore[reportUnusedExpression, reportOperatorIssue]
            return obj
        msg = f"Unsupported type for deserialization: {typ}"
        raise TypeError(msg)

    stream = QDataStream(byte_array, QIODevice.OpenModeFlag.ReadOnly)
    return tuple(_read_value(stream, i) for i in types)
