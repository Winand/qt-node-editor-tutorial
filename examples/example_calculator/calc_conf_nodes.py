from pathlib import Path
from typing import override

from calc_conf import Opcode, register_node
from calc_node_base import CalcGraphicsNode, CalcNode
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLabel, QLineEdit

from qt_node_editor.node_content_widget import (
    ContentSerialize,
    QDMContentWidget,
)
from qt_node_editor.node_scene import Scene
from qt_node_editor.node_serializable import SerializableMap


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


@register_node
class CalcNodeInput(CalcNode):
    "Input data node."
    content: "CalcInputContent"
    icon = Path("icons/in.png")
    opcode = Opcode.Input
    optitle = "Input"
    content_label_objname = "calc_node_input"

    def __init__(self, scene: Scene) -> None:
        "Set output socket."
        super().__init__(scene, inputs=[], outputs=[3])

    @override
    def init_gui_objects(self) -> None:
        self.content = CalcInputContent(self)  # FIXME: no parent?
        self.gr_node = CalcGraphicsNode(self)  # FIXME: no parent?

class InputContentSerialize(ContentSerialize):
    "Content serialization structure extended for the Input node."
    value: str

class CalcInputContent(QDMContentWidget[CalcNodeInput]):
    "Content widget for CalcNodeInput node."
    @override
    def init_ui(self) -> None:
        edit = self.edit = QLineEdit("1", self)
        edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        edit.setObjectName(self.node.content_label_objname)

    @override
    def serialize(self) -> InputContentSerialize:
        return {**super().serialize(), "value": self.edit.text()}

    @override
    def deserialize(self, data: InputContentSerialize, hashmap: SerializableMap,  # pyright: ignore[reportIncompatibleMethodOverride]
                    ) -> bool:
        res = super().deserialize(data, hashmap)
        self.edit.setText(data["value"])
        return res


@register_node
class CalcNodeOutput(CalcNode):
    "Output node."
    content: "CalcOutputContent"
    icon = Path("icons/out.png")
    opcode = Opcode.Output
    optitle = "Output"
    content_label_objname = "calc_node_output"

    def __init__(self, scene: Scene) -> None:
        "Set input socket."
        super().__init__(scene, inputs=[1], outputs=[])

    @override
    def init_gui_objects(self) -> None:
        self.content = CalcOutputContent(self)  # FIXME: no parent?
        self.gr_node = CalcGraphicsNode(self)  # FIXME: no parent?

class CalcOutputContent(QDMContentWidget[CalcNodeOutput]):
    "Content widget for CalcNodeOutput node."
    @override
    def init_ui(self) -> None:
        lbl = self.lbl = QLabel("42", self)
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lbl.setObjectName(self.node.content_label_objname)
