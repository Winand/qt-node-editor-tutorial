from qtpy.QtCore import Qt, QPointF
from qtpy.QtGui import QColor, QPainter, QPainterPath, QPen
from qtpy.QtWidgets import QGraphicsItem, QGraphicsPathItem, QStyleOptionGraphicsItem, QWidget

GraphicsItemFlag = QGraphicsItem.GraphicsItemFlag


class QDMGraphicsEdge(QGraphicsPathItem):
    "Representation of an edge between nodes."
    def __init__(self, edge, parent=None):
        super().__init__(parent)
        self.edge = edge
        self._color = QColor("#001000")
        self._color_selected = QColor("#00ff00")
        self._pen = QPen(self._color)
        self._pen_selected = QPen(self._color_selected)
        self._pen.setWidthF(2.0)
        self._pen_selected.setWidthF(2.0)

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
        painter.setPen(self._pen_selected if self.isSelected() else self._pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())

    def update_path(self):
        "Handles drawing QPainterPath from point A to B"
        raise NotImplementedError("This method has to be overridden in a child class")


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
        if s[0] > d[0]:
            dist = -dist

        path = QPainterPath(QPointF(s[0], s[1]))
        path.cubicTo(
            s[0] + dist, s[1], d[0] - dist, d[1],
            self.pos_destination[0], self.pos_destination[1]
        )
        self.setPath(path)
