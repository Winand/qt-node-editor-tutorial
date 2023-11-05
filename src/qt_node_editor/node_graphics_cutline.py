import typing
from PyQt6 import QtGui
from qtpy.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from qtpy.QtWidgets import *
from qtpy.QtGui import *
from qtpy.QtCore import *

class QDMCutLine(QGraphicsItem):
    def __init__(self, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)

        self.line_points = []

        self._pen = QPen(Qt.GlobalColor.white)
        self._pen.setWidthF(2.0)
        self._pen.setDashPattern([3, 3])

        self.setZValue(2)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, 1, 1)
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem | None, widget: QWidget | None = None) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(self._pen)

        poly = QPolygonF(self.line_points)
        painter.drawPolyline(poly)
        # return super().paint(painter, option, widget)
