from qtpy.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from qtpy.QtWidgets import *
from qtpy.QtGui import *
from qtpy.QtCore import *


class QDMCutLine(QGraphicsItem):  # TODO: QGraphicsPathItem like Edge?
    def __init__(self, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)

        self.line_points: list[QPointF] = []

        self._pen = QPen(Qt.GlobalColor.white)
        self._pen.setWidthF(2.0)
        self._pen.setDashPattern([3, 3])

        self.setZValue(2)

    @property
    def polygon(self) -> QPolygonF:
        return QPolygonF(self.line_points)

    def boundingRect(self) -> QRectF:
        return self.polygon.boundingRect()

    # TODO: May be required for collision detection with edges
    # def shape(self) -> QPainterPath:
    #     p = QPainterPath()
    #     p.addPolygon(self.polygon)
    #     return p

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem | None, widget: QWidget | None = None) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(self._pen)

        painter.drawPolyline(self.polygon)
        # return super().paint(painter, option, widget)
