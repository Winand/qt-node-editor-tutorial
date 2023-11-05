import math
# https://adamj.eu/tech/2021/05/13/python-type-hints-how-to-fix-circular-imports/
from typing import TYPE_CHECKING

from qtpy.QtCore import QLine, QObject, QRectF
from qtpy.QtGui import QColor, QPainter, QPen
from qtpy.QtWidgets import QGraphicsScene

if TYPE_CHECKING:
    from qt_node_editor.node_scene import Scene


class QDMGraphicsScene(QGraphicsScene):
    def __init__(self, scene: "Scene", parent: QObject | None = None):
        super().__init__(parent)

        self.scene = scene

        # settings
        self.grid_size = 20
        self.grid_squares = 5
        self._color_background = QColor("#393939")
        self._color_light = QColor("#2f2f2f")
        self._color_dark = QColor("#292929")

        self._pen_light = QPen(self._color_light)
        self._pen_light.setWidth(1)
        self._pen_dark = QPen(self._color_dark)
        self._pen_dark.setWidth(2)

        self.setBackgroundBrush(self._color_background)

    def set_rect(self, width: int, height: int):
        """
        Set scene rect with center in x=0, y=0.
        """
        self.setSceneRect(-width // 2, -height // 2, width, height)

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        super().drawBackground(painter, rect)

        left = int(math.floor(rect.left()))
        right = int(math.ceil(rect.right()))
        top = int(math.floor(rect.top()))
        bottom = int(math.ceil(rect.bottom()))

        first_left = left - (left % self.grid_size)
        first_top = top - (top % self.grid_size)

        lines_light, lines_dark = [], []
        for x in range(first_left, right, self.grid_size):
            if x % (self.grid_size * self.grid_squares) != 0:
                lines_light.append(QLine(x, top, x, bottom))
            else:
                lines_dark.append(QLine(x, top, x, bottom))
        for y in range(first_top, bottom, self.grid_size):
            if y % (self.grid_size * self.grid_squares) != 0:
                lines_light.append(QLine(left, y, right, y))
            else:
                lines_dark.append(QLine(left, y, right, y))

        # get scale https://forum.qt.io/topic/7486/solved-qgraphicsview-and-scale/3
        scale_factor = painter.transform().m11()  # m22
        # check if there are any lines, or `drawLines` crashes
        if lines_light and scale_factor > 0.5:
            # self._color_light.setAlphaF(scale_factor)
            # self._pen_light.setColor(self._color_light)
            painter.setPen(self._pen_light)
            # see also sip.array https://github.com/pyqtgraph/pyqtgraph/blob/906749fc0ab1334a3323d6a9c973a8fad70f3a5b/pyqtgraph/Qt/internals.py#L82
            painter.drawLines(*lines_light)
        if lines_dark:
            painter.setPen(self._pen_dark)
            painter.drawLines(*lines_dark)
