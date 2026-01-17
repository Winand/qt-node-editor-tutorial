"Module for cutting line class."
from typing import override

from qtpy.QtCore import QPointF, QRectF, Qt
from qtpy.QtGui import QPainter, QPen, QPolygonF
from qtpy.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget


class QDMCutLine(QGraphicsItem):  # TODO: QGraphicsPathItem like Edge?
    "Cutting line allows to cut several edges with single storke."

    def __init__(self, parent: QGraphicsItem | None = None) -> None:
        """
        Initialize :class:`QDMCutLine`.

        :param parent: parent graphics item
        """
        super().__init__(parent)

        #: List of points which this line consist of.
        #: ``update()`` call is required after modification.
        self.line_points: list[QPointF] = []

        self._pen = QPen(Qt.GlobalColor.white)
        self._pen.setWidthF(2.0)
        self._pen.setDashPattern([3, 3])

        self.setZValue(2)

    @property
    def polygon(self) -> QPolygonF:
        "Convert the list of points of the cutting line to a polygon."
        return QPolygonF(self.line_points)

    @override
    def boundingRect(self) -> QRectF:
        "Outer bounds of the cutting line."
        return self.polygon.boundingRect()

    # TODO: May be required for collision detection with edges
    # def shape(self) -> QPainterPath:
    #     p = QPainterPath()
    #     p.addPolygon(self.polygon)
    #     return p

    @override
    def paint(self, painter: QPainter | None, option: QStyleOptionGraphicsItem | None,
              widget: QWidget | None = None) -> None:
        "Paint the cutting line."
        assert painter
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(self._pen)

        painter.drawPolyline(self.polygon)
        # return super().paint(painter, option, widget)
