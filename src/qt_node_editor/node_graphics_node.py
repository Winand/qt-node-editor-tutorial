"Representation of a :class:`.Node` in a graphics scene."

from typing import TYPE_CHECKING, override

from qtpy.QtCore import QRectF, Qt
from qtpy.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from qtpy.QtWidgets import (
    QGraphicsItem,
    QGraphicsProxyWidget,
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent,
    QGraphicsTextItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

from qt_node_editor.utils import brush, color

if TYPE_CHECKING:
    from qt_node_editor.node_node import Node

GraphicsItemFlag = QGraphicsItem.GraphicsItemFlag


class QDMGraphicsNode(QGraphicsItem):
    "Representation of a node in a graphics scene."

    def __init__(self, node: "Node", parent: QGraphicsItem | None = None) -> None:
        """
        Initialize :class:`QDMGraphicsNode`.

        :param node: reference to a :class:`.Node` instance
        :param parent: parent graphics item or ``None``
        """
        super().__init__(parent)
        self.node = node  #: reference to a :class:`.Node` instance
        self.content = node.content  #: reference to a :class:`.Node` content widget

        # init flags
        self.hovered = False
        self._was_moved = False
        # self._last_selected_state = False

        self.init_sizes()
        self.init_assets()
        self._init_ui()

    @property
    def title(self) -> str:
        "Text in node header area."
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = value
        self.title_item.setPlainText(self._title)

    def _init_ui(self) -> None:
        "Set up graphics node (flags, title, content)."
        self.setFlag(GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(GraphicsItemFlag.ItemIsMovable)
        self.setAcceptHoverEvents(True)  # activate hover*Event

        self._init_title()  # TODO: pass _title_color, _title_font, _padding in args
        self.title = self.node.title

        self._init_content()

    def init_sizes(self) -> None:
        "Set up size properties (width, height, padding, etc)."
        self.width = 180
        self.height = 240
        self.edge_roundness = 10.0
        self.edge_padding = 10.0
        self.title_height = 24.0
        self.title_horizontal_padding = 4.0
        self.socket_vertical_padding = 10.0

    def init_assets(self) -> None:
        "Initialize colors, pens, brushes."
        # QColor format: "#[AA]RRGGBB" https://doc.qt.io/qt-6/qcolor.html#fromString
        self._color = color("#0000007f")
        self._color_selected = QColor("#ffa637")
        self._color_hovered = QColor("#2879BC")

        self._pen_default = QPen(self._color)
        self._pen_default.setWidthF(2.0)
        self._pen_selected = QPen(self._color_selected)
        self._pen_selected.setWidthF(2.0)
        self._pen_hovered = QPen(self._color_hovered)
        self._pen_hovered.setWidthF(2.0)
        self._brush_title = brush("#313131")
        self._brush_background = brush("#212121E3")

        self._title_color = Qt.GlobalColor.white
        # https://rigaux.org/font-family-compatibility-between-linux-.html
        self._title_font = QFont("Helvetica", 10)

    # def on_selected(self) -> None:
    #     self.node.scene.gr_scene.item_selected.emit()

    @override
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        "Handle mouse press&move event. Update location of connected edges."
        super().mouseMoveEvent(event)
        # FIXME: optimize
        for node in self.node.scene.nodes:
            if node.gr_node.isSelected():
                node.update_connected_edges()
        self._was_moved = True

    @override
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        "Handle mouse release event. Store node move action in history."
        super().mouseReleaseEvent(event)
        if self._was_moved:
            self._was_moved = False
            self.node.scene.history.store_history("Node moved", modified=True)
        #     self.node.scene.reset_last_selected_states()
        #     self._last_selected_state = True
        #     # store the last selected state, because moving does also selct the nodes
        #     self.node.scene.last_selected_items = self.node.scene.get_selected_items()
        # elif (
        #     self._last_selected_state != self.isSelected() or
        #     self.node.scene.last_selected_items != self.node.scene.get_selected_items
        # ):
        #     self.node.scene.reset_last_selected_states()
        #     self._last_selected_state = self.isSelected()
        #     self.on_selected()

    @override
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent | None) -> None:
        self.hovered = True
        self.update()

    @override
    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent | None) -> None:
        self.hovered = False
        self.update()

    @override
    def boundingRect(self) -> QRectF:  # required
        "Outer bounds of the item."
        return QRectF(0, 0, self.width, self.height) \
            .normalized()  # swap values if width/height is negative (needed?)

    def _init_title(self) -> None:
        "Initialize font and color of a node title."
        self.title_item = QGraphicsTextItem(self)
        # self.title_item.node = self.node  # https://gitlab.com/pavel.krupala/pyqt-node-editor/-/blob/master/nodeeditor/node_graphics_node.py?ref_type=heads#L172
        self.title_item.setObjectName("title")  # identify on click
        # self.title_item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.title_item.setDefaultTextColor(self._title_color)
        self.title_item.setFont(self._title_font)
        self.title_item.setPos(self.title_horizontal_padding, 0)
        self.title_item.setTextWidth(self.width - 2 * self.title_horizontal_padding)

    def _init_content(self) -> None:
        "Set up proxy widget containing the content widget."
        self.gr_content = QGraphicsProxyWidget(self)
        self.content.setGeometry(
            int(self.edge_padding), int(self.title_height + self.edge_padding),
            int(self.width - 2 * self.edge_padding),
            int(self.height - 2 * self.edge_padding - self.title_height),
        )
        self.gr_content.setWidget(self.content)

    def paint(self, painter: QPainter | None, option: QStyleOptionGraphicsItem | None,
              widget: QWidget | None = None) -> None:  # required
        "Paint title, content and outline."
        assert painter
        # Title ->
        path_title = QPainterPath()
        # WindingFill/OddEvenFill affects intersection of rects in a path
        # https://en.wikipedia.org/wiki/Even%E2%80%93odd_rule
        path_title.setFillRule(Qt.FillRule.WindingFill)
        path_title.addRoundedRect(0, 0, self.width, self.title_height,
                                  self.edge_roundness, self.edge_roundness)
        # Draw rect over lower part of the title to make it not rounded
        path_title.addRect(0, self.title_height - self.edge_roundness, self.width,
                           self.edge_roundness)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._brush_title)
        painter.drawPath(path_title.simplified())

        # Contents ->
        path_content = QPainterPath()
        path_content.setFillRule(Qt.FillRule.WindingFill)
        path_content.addRoundedRect(0, self.title_height, self.width,
                                    self.height - self.title_height,
                                    self.edge_roundness, self.edge_roundness)
        path_content.addRect(0, self.title_height, self.width, self.edge_roundness)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._brush_background)
        painter.drawPath(path_content.simplified())

        # Outline ->
        path_outline = QPainterPath()
        path_outline.addRoundedRect(0, 0, self.width, self.height,
                                    self.edge_roundness, self.edge_roundness)
        # https://doc.qt.io/qt-6/qpainterpath.html#simplified
        painter.setPen(self._pen_selected if self.isSelected() else
                       self._pen_default)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path_outline.simplified())
        if self.hovered and not self.isSelected():
            painter.setPen(self._pen_hovered)
            painter.drawPath(path_outline.simplified())
