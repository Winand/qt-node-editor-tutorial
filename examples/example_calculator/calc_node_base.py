import logging
from pathlib import Path
from typing import Any, final, override

from calc_conf import Opcode
from qtpy.QtCore import QPointF, QRectF
from qtpy.QtGui import QIcon, QImage, QPainter
from qtpy.QtWidgets import QLabel, QStyleOptionGraphicsItem, QWidget

from qt_node_editor.node_content_widget import QDMContentWidget
from qt_node_editor.node_edge import Edge
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

    @override
    def init_assets(self) -> None:
        super().init_assets()
        self.icons = QImage(str(Path(__file__).parent / "icons/status_icons.png"))

    @override
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem,  # type: ignore[reportIncompatibleMethodOverride]
              widget: QWidget | None = None) -> None:
        super().paint(painter, option, widget)

        offset = 24
        if self.node.is_invalid():
            offset = 48
        elif self.node.is_dirty():
            offset = 0
        painter.drawImage(QPointF(-10, -10), self.icons, QRectF(offset, 0, 24, 24))


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
        self.value = None
        self.mark_dirty()

    @override
    def init_gui_objects(self) -> None:
        self.content = CalcContent(self)  # FIXME: no parent?
        self.gr_node = CalcGraphicsNode(self)  # FIXME: no parent?

    @override
    def init_settings(self) -> None:
        super().init_settings()
        self.input_socket_position = Pos.LEFT_CENTER
        self.output_socket_position = Pos.RIGHT_CENTER

    def eval_operation(self, input1: float, input2: float) -> float:
        return 123

    def eval_impl(self) -> Any:
        i1 = self.get_input(0)
        i2 = self.get_input(1)
        if not i1 or not i2:
            msg = "Some inputs not connected"
            raise ValueError(msg)
        self.value = self.eval_operation(i1.eval(), i2.eval())
        self.mark_dirty(unset=True)
        self.mark_invalid(unset=True)
        self.mark_descendants_dirty()
        self.eval_children()  # FIXME: eval all descendants?
        return self.value

    @final
    @override
    def eval(self) -> Any:
        if not self.is_dirty() and not self.is_invalid():
            log.info("Cached %s eval value %s:", self.__class__.__name__, self.value)
            return self.value
        self.gr_node.setToolTip(None)
        try:
            return self.eval_impl()
        except ValueError as e:
            self.mark_invalid()
            self.gr_node.setToolTip(str(e))
            self.mark_descendants_dirty()
        except Exception as e:
            self.mark_invalid()
            self.gr_node.setToolTip(str(e))
            log.exception("Node eval exception")

    @override
    def on_input_data_changed(self, edge: Edge) -> None:
        log.info("%s::on_input_data_changed", self.__class__.__name__)
        self.mark_dirty()
        self.eval()

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
