from pathlib import Path

from calc_conf import Opcode, register_node
from calc_node_base import CalcNode

from qt_node_editor.node_scene import Scene


@register_node
class CalcNodeAdd(CalcNode):
    "Sum two values node."
    icon = Path("icons/add.png")
    opcode = Opcode.Add
    optitle = "Add"
    content_label = "+"


@register_node
class CalcNodeSubtract(CalcNode):
    "Subtract a value node."
    icon = Path("icons/sub.png")
    opcode = Opcode.Subtract
    optitle = "Subtract"
    content_label = "-"


@register_node
class CalcNodeMultiply(CalcNode):
    "Multiply values node."
    icon = Path("icons/mul.png")
    opcode = Opcode.Multiply
    optitle = "Multiply"
    content_label = "*"


@register_node
class CalcNodeDivide(CalcNode):
    "Divide a value node."
    icon = Path("icons/divide.png")
    opcode = Opcode.Divide
    optitle = "Divide"
    content_label = "/"


@register_node
class CalcNodeInput(CalcNode):
    "Input data node."
    icon = Path("icons/in.png")
    opcode = Opcode.Input
    optitle = "Input"

    def __init__(self, scene: Scene) -> None:
        "Set output socket."
        super().__init__(scene, inputs=[], outputs=[3])


@register_node
class CalcNodeOutput(CalcNode):
    "Output node."
    icon = Path("icons/out.png")
    opcode = Opcode.Output
    optitle = "Output"

    def __init__(self, scene: Scene) -> None:
        "Set input socket."
        super().__init__(scene, inputs=[1], outputs=[])
