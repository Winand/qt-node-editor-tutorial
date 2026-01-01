from pathlib import Path
from typing import override

from calc_conf import Opcode
from qtpy.QtWidgets import QLabel

from qt_node_editor.node_content_widget import QDMContentWidget
from qt_node_editor.node_graphics_node import QDMGraphicsNode
from qt_node_editor.node_node import Node
from qt_node_editor.node_scene import Scene


class CalcGraphicsNode(QDMGraphicsNode):
    @override
    def init_sizes(self) -> None:
        super().init_sizes()
        self.width = 160
        self.height = 74
        self.edge_size = 5.0
        self._padding = 8.0  # title x-padding


class CalcContent(QDMContentWidget["CalcNode"]):
    @override
    def init_ui(self) -> None:
        lbl = QLabel(self.node.content_label, self)
        lbl.setObjectName(self.node.content_label_objname)


class CalcNode(Node):
    "Base class for nodes."
    icon: Path | None = None
    opcode = Opcode.Unset
    optitle = "Undefined"
    content_label = ""
    content_label_objname = "calc_node_bg"

    def __init__(self, scene: Scene,
                 inputs: list[int] | None = None,
                 outputs: list[int] | None = None) -> None:
        inputs = [2, 2] if inputs is None else inputs
        outputs = [1] if outputs is None else outputs
        super().__init__(scene, self.optitle, inputs, outputs)

    @override
    def init_gui_objects(self) -> None:
        self.content = CalcContent(self)
        self.gr_node = CalcGraphicsNode(self)
