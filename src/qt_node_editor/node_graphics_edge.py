import math
from typing import TYPE_CHECKING

from qtpy.QtCore import QPointF, Qt
from qtpy.QtGui import QColor, QPainter, QPainterPath, QPainterPathStroker, QPen
from qtpy.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

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
        # init flags
        # self._last_selected_state = False
        # init variables
        self.pos_source = [0, 0]
        self.pos_destination = [100, 100]

        self.init_assets()
        self.init_ui()

    def init_ui(self) -> None:
        self.setFlag(GraphicsItemFlag.ItemIsSelectable)
        self.setZValue(-1)  # place under nodes

    def init_assets(self) -> None:
        self._color = QColor("#001000")
        self._color_selected = QColor("#00ff00")
        self._pen = QPen(self._color)
        self._pen_selected = QPen(self._color_selected)
        self._pen_dragging = QPen(self._color)
        self._pen_dragging.setStyle(Qt.PenStyle.DashLine)
        self._pen.setWidthF(2.0)
        self._pen_selected.setWidthF(2.0)
        self._pen_dragging.setWidthF(2.0)

    # def on_selected(self) -> None:
    #     self.edge.scene.gr_scene.item_selected.emit()

    # @override
    # def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
    #     super().mouseReleaseEvent(event)
    #     if self._last_selected_state != self.isSelected():
    #         self.edge.scene.reset_last_selected_states()
    #         self._last_selected_state = self.isSelected()
    #         self.on_selected()

    def set_source(self, x, y):
        self.pos_source = [x, y]

    def set_destination(self, x, y):
        self.pos_destination = [x, y]

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem | None,
              widget: QWidget | None = None) -> None:
        self.setPath(self.calc_path())
        if self.edge.end_socket is None:
            painter.setPen(self._pen_dragging)
        else:
            painter.setPen(self._pen_selected if self.isSelected() else self._pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())

    def intersects_with(self, p1: QPointF, p2: QPointF):
        cutpath = QPainterPath(p1)
        cutpath.lineTo(p2)
        path = self.calc_path()
        return cutpath.intersects(path)

    def calc_path(self) -> QPainterPath:
        "Handles drawing QPainterPath from point A to B"
        raise NotImplementedError("This method has to be overridden in a child class")

    # boundingRect() is calculated from shape() if it is implemented correctly.
    # If it is required to paint() something outside of the shape() this rect
    # needs to be adjusted. | https://youtu.be/FPP4RcGeQpU?t=33

    def shape(self) -> QPainterPath:
        "Shape is a clickable area of the Item."
        # By default shape() is a closed path(), see example image in docs
        # https://doc.qt.io/qt-6/qgraphicspathitem.html#details.
        stroker = QPainterPathStroker()  # creates a fillable shape from path
        stroker.setWidth(8)  # wider path is easier to click
        stroker.setCapStyle(Qt.PenCapStyle.FlatCap)  # do not add width/2 margin to ends
        return stroker.createStroke(self.path())


class QDMGraphicsEdgeDirect(QDMGraphicsEdge):
    def calc_path(self) -> QPainterPath:
        path = QPainterPath(QPointF(self.pos_source[0], self.pos_source[1]))
        path.lineTo(self.pos_destination[0], self.pos_destination[1])
        return path


class QDMGraphicsEdgeBezier(QDMGraphicsEdge):
    def calc_path(self) -> QPainterPath:
        s = self.pos_source
        d = self.pos_destination
        dist = (d[0] - s[0]) * 0.5

        cpx_s = +dist
        cpx_d = -dist
        cpy_s = 0
        cpy_d = 0

        if not self.edge.start_socket:
            raise ValueError  # see also https://gitlab.com/pavel.krupala/pyqt-node-editor/-/blob/master/nodeeditor/node_graphics_edge_path.py#L60
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
        return path
