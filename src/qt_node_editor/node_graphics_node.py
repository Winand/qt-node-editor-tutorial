"""
Representation of a node in a graphics scene.
"""

from typing import TYPE_CHECKING

from qtpy.QtCore import QRectF, Qt
from qtpy.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from qtpy.QtWidgets import (QGraphicsItem, QGraphicsTextItem,
                            QStyleOptionGraphicsItem, QWidget)

if TYPE_CHECKING:
    from qt_node_editor.node_node import Node

GraphicsItemFlag = QGraphicsItem.GraphicsItemFlag


class QDMGraphicsNode(QGraphicsItem):
    def __init__(self, node: "Node", title="Node Graphic Item",
                 parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)

        self.width = 180
        self.height = 240
        self.edge_size = 10.0
        self.title_height = 24.0
        self._padding = 4.0

        self._pen_default = QPen(QColor("#7F000000"))
        self._pen_selected = QPen(QColor("#FFFFA637"))
        self._brush_title = QBrush(QColor("#FF313131"))
        self._brush_background = QBrush(QColor("#E3212121"))

        self._title_color = Qt.GlobalColor.white
        # https://rigaux.org/font-family-compatibility-between-linux-.html
        self._title_font = QFont("Helvetica", 10)
        self.init_title()
        self.title = title

        self.init_ui()

    def boundingRect(self) -> QRectF:  # required
        """
        Outer bounds of the item.
        """
        return QRectF(0, 0,
                      2 * self.edge_size + self.width,
                      2 * self.edge_size + self.height
                      ).normalized()  # swap values if width/height is negative

    def init_ui(self):
        self.setFlag(GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(GraphicsItemFlag.ItemIsMovable)

    def init_title(self):
        """
        Initialize font and color of a node title.
        """
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setDefaultTextColor(self._title_color)
        self.title_item.setFont(self._title_font)
        self.title_item.setPos(self._padding, 0)
        self.title_item.setTextWidth(
            self.width - 2 * self._padding
        )

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value: str):
        self._title = value
        self.title_item.setPlainText(self._title)

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
