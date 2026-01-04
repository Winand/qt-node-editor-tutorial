"Operations nodes."

from pathlib import Path

from calc_conf import Opcode, register_node
from calc_node_base import CalcNode


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
    content_label_objname = "calc_node_mul"


@register_node
class CalcNodeDivide(CalcNode):
    "Divide a value node."
    icon = Path("icons/divide.png")
    opcode = Opcode.Divide
    optitle = "Divide"
    content_label = "/"
    content_label_objname = "calc_node_div"
