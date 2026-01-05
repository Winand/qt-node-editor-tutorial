"Data output node."

from pathlib import Path
from typing import Any, override

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

    @override
    def eval_impl(self) -> Any:
        if not (input_node := self.get_input(0)):
            msg = "Input is not connected"
            raise ValueError(msg)
        if (val := input_node.eval()) is None:
            msg = "Input is NaN"
            raise ValueError(msg)
        str_result = f"{val:.7g}" if isinstance(val, float) else str(val)
        self.content.lbl.setText(str_result)
        self.mark_invalid(unset=True)
        self.mark_dirty(unset=True)
        return val


class CalcOutputContent(QDMContentWidget[CalcNodeOutput]):
    "Content widget for CalcNodeOutput node."
    @override
    def init_ui(self) -> None:
        lbl = self.lbl = QLabel("42", self)
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lbl.setObjectName(self.node.content_label_objname)
