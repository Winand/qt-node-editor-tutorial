"Data output node."

from pathlib import Path
from typing import override

from calc_conf import Opcode, register_node
from calc_node_base import CalcGraphicsNode, CalcNode
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLabel

from qt_node_editor.node_content_widget import QDMContentWidget
from qt_node_editor.node_scene import Scene


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
