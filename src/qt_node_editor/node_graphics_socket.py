"Module for a graphical representation of a :class:`.Socket`."
from typing import TYPE_CHECKING, override

from qtpy.QtCore import QRectF, Qt
from qtpy.QtGui import QBrush, QColor, QPainter, QPen
from qtpy.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget

if TYPE_CHECKING:
    from qt_node_editor.node_socket import Socket

SOCKET_COLORS = [
    QColor("#FF7700"),
    QColor("#52E220"),
    QColor("#0056A6"),
    QColor("#A86DB1"),
    QColor("#B54747"),
    QColor("#DBE220"),
    QColor("#888888"),
]
"""
:class:`.Socket` color list. Color names: https://colornamer.robertcooper.me.

0. lucky orange
1. green apple
2. raiden blue
3. soft purple
4. baked apple (red)
5. poisonous icecream (yellow)
6. argent (grey)
"""


class QDMGraphicsSocket(QGraphicsItem):
    "Graphical representation of a :class:`.Socket` in a ``QGraphicsScene``."

    def __init__(self, socket: "Socket", socket_type: int = 1) -> None:
        """
        Initialize ``QDMGraphicsSocket``.

        :param socket: reference to :class:`.Socket`
        :type socket: Socket
        :param socket_type: Const
        :type socket_type: int
        """
        super().__init__(socket.node.gr_node)
        self.socket = socket
        self.socket_type = socket_type

        self.radius = 6.0
        self.outline_width = 1.0
        self.init_assets()

    def _get_socket_color(self, key: int | str) -> QColor:
        "Return the ``QColor`` for the passed key or index."
        if isinstance(key, int):
            return SOCKET_COLORS[key]
        if isinstance(key, str):
            return QColor(key)
        return Qt.GlobalColor.transparent

    def init_assets(self) -> None:
        "Initialize internal objects like color, pen, brush."
        self._color_background = self._get_socket_color(self.socket_type)
        self._color_outline = QColor("#FF000000")

        self._pen = QPen(self._color_outline)
        self._pen.setWidthF(self.outline_width)
        self._brush = QBrush(self._color_background)

    @override
    def paint(self, painter: QPainter | None, option: QStyleOptionGraphicsItem | None,
              widget: QWidget | None = None) -> None:
        "Paint a circle."
        assert painter
        painter.setBrush(self._brush)
        painter.setPen(self._pen)
        painter.drawEllipse(QRectF(-self.radius, -self.radius,
                                   2 * self.radius, 2 * self.radius))

    @override
    def boundingRect(self) -> QRectF:
        "Define `radius + outline_width` around zero point."
        return QRectF(
            -self.radius - self.outline_width,
            -self.radius - self.outline_width,
            2 * (self.radius + self.outline_width),
            2 * (self.radius + self.outline_width),
        )
