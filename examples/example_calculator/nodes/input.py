"Data input node."

from pathlib import Path
from typing import Any, override

from calc_conf import Opcode, register_node
from calc_node_base import CalcGraphicsNode, CalcNode
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLineEdit

from qt_node_editor.node_content_widget import (
    ContentSerialize,
    QDMContentWidget,
)
from qt_node_editor.node_scene import Scene
from qt_node_editor.node_serializable import SerializableMap


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
        self.eval()

    @override
    def init_gui_objects(self) -> None:
        self.content = CalcInputContent(self)  # FIXME: no parent?
        self.gr_node = CalcGraphicsNode(self)  # FIXME: no parent?
        self.content.edit.textChanged.connect(self.on_input_data_changed)

    @override
    def eval_impl(self) -> Any:
        self.value = int(self.content.edit.text())
        self.mark_dirty(unset=True)
        self.mark_invalid(unset=True)
        self.mark_descendants_invalid(unset=True)
        self.mark_descendants_dirty()
        self.eval_children()  # FIXME: eval all descendants?
        return self.value


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
