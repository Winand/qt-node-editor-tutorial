from qtpy.QtCore import QRectF
from qtpy.QtGui import QBrush, QColor, QPainter, QPen
from qtpy.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget


class QDMGraphicsSocket(QGraphicsItem):
    def __init__(self, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)

        self.radius = 6.0
        self.outline_width = 1.0
        self._color_background = QColor("#FFFF7700")
        self._color_outline = QColor("#FF000000")

        self._pen = QPen(self._color_outline)
        self._pen.setWidthF(self.outline_width)
        self._brush = QBrush(self._color_background)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem | None,
              widget: QWidget | None = None) -> None:
        painter.setBrush(self._brush)
        painter.setPen(self._pen)
        painter.drawEllipse(QRectF(-self.radius, -self.radius,
                                   2 * self.radius, 2 * self.radius))

    def boundingRect(self) -> QRectF:
        "`radius + outline_width` around zero point"
        return QRectF(
            -self.radius - self.outline_width,
            -self.radius - self.outline_width,
            2 * (self.radius + self.outline_width),
            2 * (self.radius + self.outline_width)
        )
