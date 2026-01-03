import logging
from pathlib import Path
from typing import override

from calc_conf import Opcode
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QLabel

from qt_node_editor.node_content_widget import QDMContentWidget
from qt_node_editor.node_graphics_node import QDMGraphicsNode
from qt_node_editor.node_node import Node, NodeSerialize
from qt_node_editor.node_scene import Scene
from qt_node_editor.node_serializable import SerializableMap
from qt_node_editor.node_socket import Pos

log = logging.getLogger(__name__)


class CalcNodeSerialize(NodeSerialize):
    "Node serialization structure extended for CalcNode."
    opcode: Opcode


class CalcGraphicsNode(QDMGraphicsNode):
    @override
    def init_sizes(self) -> None:
        super().init_sizes()
        self.width = 160
        self.height = 74
        self.edge_roundness = 6.0
        self.edge_padding = 0.0
        self.title_horizontal_padding = 8.0


class CalcContent(QDMContentWidget["CalcNode"]):
    @override
    def init_ui(self) -> None:
        lbl = QLabel(self.node.content_label, self)
        lbl.setObjectName(self.node.content_label_objname)  # TODO: what is it for?


class CalcNode(Node):
    "Base class for calculator nodes."
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
        self.content = CalcContent(self)  # FIXME: no parent?
        self.gr_node = CalcGraphicsNode(self)  # FIXME: no parent?

    @override
    def init_settings(self) -> None:
        super().init_settings()
        self.input_socket_position = Pos.LEFT_CENTER
        self.output_socket_position = Pos.RIGHT_CENTER

    @classmethod
    def get_icon(cls) -> QIcon:
        "Get an icon for the node, may be empty icon."
        return QIcon(str(Path(__file__).parent / cls.icon) if cls.icon else ".")

    @override
    def serialize(self) -> CalcNodeSerialize:
        return {**super().serialize(), "opcode": self.opcode}

    @override
    def deserialize(self, data: CalcNodeSerialize, hashmap: SerializableMap,  # pyright: ignore[reportIncompatibleMethodOverride]
                    restore_id: bool = True) -> bool:
        res = super().deserialize(data, hashmap, restore_id)
        log.debug("Deserialized CalcNode '%s', res:%s", self.__class__.__name__, res)
        return res
