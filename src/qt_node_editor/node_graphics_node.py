"""
Representation of a node in a graphics scene.
"""

from typing import TYPE_CHECKING, override

from qtpy.QtCore import QRectF, Qt
from qtpy.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from qtpy.QtWidgets import (
    QGraphicsItem,
    QGraphicsProxyWidget,
    QGraphicsSceneMouseEvent,
    QGraphicsTextItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

if TYPE_CHECKING:
    from qt_node_editor.node_node import Node

GraphicsItemFlag = QGraphicsItem.GraphicsItemFlag


class QDMGraphicsNode(QGraphicsItem):
    "Representation of a node in a graphics scene."
    def __init__(self, node: "Node", parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self.node = node
        self.content = node.content

        # init flags
        self._was_moved = False
        # self._last_selected_state = False

        self.init_sizes()
        self.init_assets()
        self.init_ui()

    def init_ui(self):
        self.setFlag(GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(GraphicsItemFlag.ItemIsMovable)

        self.init_title()  # TODO: pass _title_color, _title_font, _padding in args
        self.title = self.node.title

        self.init_sockets()
        self.init_content()

    def init_sizes(self) -> None:
        self.width = 180
        self.height = 240
        self.edge_size = 10.0
        self.title_height = 24.0
        self._padding = 4.0  # title x-padding

    def init_assets(self) -> None:
        self._pen_default = QPen(QColor("#7F000000"))
        self._pen_selected = QPen(QColor("#FFFFA637"))
        self._brush_title = QBrush(QColor("#FF313131"))
        self._brush_background = QBrush(QColor("#E3212121"))

        self._title_color = Qt.GlobalColor.white
        # https://rigaux.org/font-family-compatibility-between-linux-.html
        self._title_font = QFont("Helvetica", 10)

    # def on_selected(self) -> None:
    #     self.node.scene.gr_scene.item_selected.emit()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        super().mouseMoveEvent(event)
        # FIXME: optimize
        for node in self.node.scene.nodes:
            if node.gr_node.isSelected():
                node.update_connected_edges()
        self._was_moved = True

    @override
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
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

    @property
    def title(self):
        "Set text in node header area."
        return self._title

    @title.setter
    def title(self, value: str):
        self._title = value
        self.title_item.setPlainText(self._title)

    def boundingRect(self) -> QRectF:  # required
        """
        Outer bounds of the item.
        """
        return QRectF(0, 0, self.width, self.height) \
            .normalized()  # swap values if width/height is negative (needed?)

    def init_title(self):
        """
        Initialize font and color of a node title.
        """
        self.title_item = QGraphicsTextItem(self)
        # self.title_item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.title_item.setDefaultTextColor(self._title_color)
        self.title_item.setFont(self._title_font)
        self.title_item.setPos(self._padding, 0)
        self.title_item.setTextWidth(
            self.width - 2 * self._padding
        )

    def init_content(self):
        self.gr_content = QGraphicsProxyWidget(self)
        self.content.setGeometry(
            int(self.edge_size), int(self.title_height + self.edge_size),
            int(self.width - 2 * self.edge_size),
            int(self.height - 2 * self.edge_size - self.title_height)
        )
        self.gr_content.setWidget(self.content)

    def init_sockets(self):
        pass

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem | None,
              widget: QWidget | None = None) -> None:  # required
        """
        Paint title, content and outline.
        """
        # Title ->
        path_title = QPainterPath()
        # WindingFill/OddEvenFill affects intersection of rects in a path
        # https://en.wikipedia.org/wiki/Even%E2%80%93odd_rule
        path_title.setFillRule(Qt.FillRule.WindingFill)
        path_title.addRoundedRect(0, 0, self.width, self.title_height,
                                  self.edge_size, self.edge_size)
        # Draw rect over lower part of the title to make it not rounded
        path_title.addRect(0, self.title_height - self.edge_size, self.width,
                           self.edge_size)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._brush_title)
        painter.drawPath(path_title.simplified())

        # Contents ->
        path_content = QPainterPath()
        path_content.setFillRule(Qt.FillRule.WindingFill)
        path_content.addRoundedRect(0, self.title_height, self.width,
                                    self.height - self.title_height,
                                    self.edge_size, self.edge_size)
        path_content.addRect(0, self.title_height, self.width, self.edge_size)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._brush_background)
        painter.drawPath(path_content.simplified())

        # Outline ->
        path_outline = QPainterPath()
        path_outline.addRoundedRect(0, 0, self.width, self.height,
                                    self.edge_size, self.edge_size)
        painter.setPen(self._pen_selected if self.isSelected() else
                       self._pen_default)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        # https://doc.qt.io/qt-6/qpainterpath.html#simplified
        painter.drawPath(path_outline.simplified())
