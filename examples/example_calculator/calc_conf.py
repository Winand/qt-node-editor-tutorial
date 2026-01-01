from enum import IntEnum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from calc_node_base import CalcNode

MIMETYPE_LISTBOX = "application/node-item"

class Opcode(IntEnum):
    Unset = 0  # stub in CalcNode base class
    Input = auto()
    Output = auto()
    Add = auto()
    Subtract = auto()
    Multiply = auto()
    Divide = auto()

CALC_NODES: dict[Opcode, type["CalcNode"]] = {}

class ConfExceptionError(Exception):
    "Configuration exception."

class InvalidNodeRegistrationError(ConfExceptionError):
    "New node registration failed."

class OpcodeNotRegisteredError(ConfExceptionError):
    "New node registration failed."


def register_node_now(class_reference: type["CalcNode"]):
    opcode = class_reference.opcode
    if opcode in CALC_NODES:
        msg = f"Failed to register {opcode}. Already registered {CALC_NODES[opcode]}"
        raise InvalidNodeRegistrationError(msg)
    CALC_NODES[opcode] = class_reference


def register_node[T: "CalcNode"](original_class: type[T]) -> type[T]:
    register_node_now(original_class)
    return original_class


def get_class_from_opcode(opcode: Opcode) -> type["CalcNode"]:
    if opcode not in CALC_NODES:
        msg = f"Opcode {opcode} not registered"
        raise OpcodeNotRegisteredError(msg)
    return CALC_NODES[opcode]
