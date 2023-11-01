import math
from typing import TYPE_CHECKING

from qtpy.QtCore import QPointF, QRectF, Qt
from qtpy.QtGui import QColor, QPainter, QPainterPath, QPen
from qtpy.QtWidgets import (QGraphicsItem, QGraphicsPathItem,
                            QStyleOptionGraphicsItem, QWidget)

from qt_node_editor.node_socket import Pos

if TYPE_CHECKING:
    from qt_node_editor.node_edge import Edge

GraphicsItemFlag = QGraphicsItem.GraphicsItemFlag

EDGE_CP_ROUNDNESS = 100

class QDMGraphicsEdge(QGraphicsPathItem):
    "Representation of an edge between nodes."
    def __init__(self, edge: "Edge", parent=None):
        super().__init__(parent)
        self.edge = edge
        self._color = QColor("#001000")
        self._color_selected = QColor("#00ff00")
        self._pen = QPen(self._color)
        self._pen_selected = QPen(self._color_selected)
        self._pen_dragging = QPen(self._color)
        self._pen_dragging.setStyle(Qt.PenStyle.DashLine)
        self._pen.setWidthF(2.0)
        self._pen_selected.setWidthF(2.0)
        self._pen_dragging.setWidthF(2.0)

        self.setFlag(GraphicsItemFlag.ItemIsSelectable)

        self.setZValue(-1)  # place under nodes

        self.pos_source = [0, 0]
        self.pos_destination = [100, 100]

    def set_source(self, x, y):
        self.pos_source = [x, y]

    def set_destination(self, x, y):
        self.pos_destination = [x, y]

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem | None,
              widget: QWidget | None = None) -> None:
        self.update_path()
        if self.edge.end_socket is None:
            painter.setPen(self._pen_dragging)
        else:
            painter.setPen(self._pen_selected if self.isSelected() else self._pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())

    def update_path(self):
        "Handles drawing QPainterPath from point A to B"
        raise NotImplementedError("This method has to be overridden in a child class")

    def boundingRect(self):
        "Returns item area (required for correct updates)"
        return QRectF(
            QPointF(*self.pos_source), QPointF(*self.pos_destination)
        ).normalized()


class QDMGraphicsEdgeDirect(QDMGraphicsEdge):
    def update_path(self):
        path = QPainterPath(QPointF(self.pos_source[0], self.pos_source[1]))
        path.lineTo(self.pos_destination[0], self.pos_destination[1])
        self.setPath(path)


class QDMGraphicsEdgeBezier(QDMGraphicsEdge):
    def update_path(self):
        s = self.pos_source
        d = self.pos_destination
        dist = (d[0] - s[0]) * 0.5

        cpx_s = +dist
        cpx_d = -dist
        cpy_s = 0
        cpy_d = 0

        if not self.edge.start_socket:
            raise ValueError
        sspos = self.edge.start_socket.position

        if (s[0] > d[0] and sspos in (Pos.RIGHT_TOP, Pos.RIGHT_BOTTOM)) or \
           (s[0] < d[0] and sspos in (Pos.LEFT_TOP, Pos.LEFT_BOTTOM)):
            cpx_d = -cpx_d
            cpx_s = -cpx_s

            cpy_d = (
                (s[1] - d[1]) / math.fabs(
                    (s[1] - d[1]) if (s[1] - d[1]) != 0 else .00001  # evade div. by 0
                )
            ) * EDGE_CP_ROUNDNESS
            cpy_s = (
                (d[1] - s[1]) / math.fabs(
                    (d[1] - s[1]) if (d[1] - s[1]) != 0 else .00001  # evade div. by 0
                )
            ) * EDGE_CP_ROUNDNESS


        path = QPainterPath(QPointF(s[0], s[1]))
        path.cubicTo(
            s[0] + cpx_s, s[1] + cpy_s, d[0] + cpx_d, d[1] + cpy_d,
            self.pos_destination[0], self.pos_destination[1]
        )
        self.setPath(path)
