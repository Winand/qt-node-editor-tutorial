"Module for a graphical representation of a :class:`.Node`."
import logging
import math

# https://adamj.eu/tech/2021/05/13/python-type-hints-how-to-fix-circular-imports/
from typing import TYPE_CHECKING, override

from qtpy import API_NAME
from qtpy.QtCore import QLine, QObject, QRectF
from qtpy.QtGui import QColor, QPainter, QPen
from qtpy.QtWidgets import QGraphicsScene

if TYPE_CHECKING:
    from qtpy.QtWidgets import QGraphicsSceneDragDropEvent

    from qt_node_editor.node_scene import Scene

log = logging.getLogger(__name__)


class QDMGraphicsScene(QGraphicsScene):
    "Class for graphical representation of a :class:`.Scene`."
    # item_selected = Signal()
    # items_deselected = Signal()

    def __init__(self, scene: "Scene", parent: QObject | None = None) -> None:
        """
        Initialize :class:`QDMGraphicsScene`.

        :param scene: reference to a :class:`.Scene` instance
        :param parent: parent widget or `None`
        """
        super().__init__(parent)

        self.scene = scene

        # settings
        self.grid_size = 20
        self.grid_squares = 5

        self._init_assets()
        self.setBackgroundBrush(self._color_background)

    def _init_assets(self) -> None:
        "Set up colors and pens."
        self._color_background = QColor("#393939")
        self._color_light = QColor("#2f2f2f")
        self._color_dark = QColor("#292929")

        self._pen_light = QPen(self._color_light)
        self._pen_light.setWidth(1)
        self._pen_dark = QPen(self._color_dark)
        self._pen_dark.setWidth(2)

    @override
    def dragMoveEvent(self, event: "QGraphicsSceneDragDropEvent | None") -> None:
        "Skip drag move event so it is processed by parent widget."  # https://youtu.be/CX7ox9v4tpc?t=981

    # TODO: make scene infinite? https://doc.qt.io/qt-6/qgraphicsscene.html#sceneRect-prop
    def set_rect(self, width: int, height: int) -> None:
        """
        Set scene rect with center in x=0, y=0.

        :param width: width of the scene
        :param height: height of the scene
        """
        self.setSceneRect(-width // 2, -height // 2, width, height)

    @override
    def drawBackground(self, painter: QPainter | None, rect: QRectF) -> None:
        "Draw scene background (grid)."
        assert painter
        super().drawBackground(painter, rect)

        left = math.floor(rect.left())
        right = math.ceil(rect.right())
        top = math.floor(rect.top())
        bottom = math.ceil(rect.bottom())

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
            if API_NAME.startswith("PyQt"):
                # see also sip.array https://github.com/pyqtgraph/pyqtgraph/blob/906749fc0ab1334a3323d6a9c973a8fad70f3a5b/pyqtgraph/Qt/internals.py#L82
                painter.drawLines(*lines_light)
            else:
                painter.drawLines(lines_light)  # pyright: ignore[reportArgumentType, reportCallIssue]
        if lines_dark:
            painter.setPen(self._pen_dark)
            if API_NAME.startswith("PyQt"):
                painter.drawLines(*lines_dark)
            else:
                painter.drawLines(lines_dark)  # pyright: ignore[reportArgumentType, reportCallIssue]

    def __del__(self) -> None:
        "Graphics scene instance destruction event."
        log.debug("delete graphics scene")
