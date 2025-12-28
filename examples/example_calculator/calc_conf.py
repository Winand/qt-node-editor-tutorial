from enum import IntEnum, auto

MIMETYPE_LISTBOX = "application/node-item"

class Opcode(IntEnum):
    Input = auto()
    Output = auto()
    Add = auto()
    Subtract = auto()
    Multiply = auto()
    Divide = auto()
