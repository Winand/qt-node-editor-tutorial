from enum import Enum, auto
from typing import TYPE_CHECKING

from qt_node_editor.node_graphics_socket import QDMGraphicsSocket

if TYPE_CHECKING:
    from qt_node_editor.node_node import Node


class POS(Enum):
    LEFT_TOP = auto()
    LEFT_BOTTOM = auto()
    RIGHT_TOP = auto()
    RIGHT_BOTTOM = auto()


class Socket():
    def __init__(self, node: "Node", index = 0, position=POS.LEFT_TOP) -> None:
        self.node = node
        self.index = index
        self.position = position
        self.gr_socket = QDMGraphicsSocket(node.gr_node)
        self.gr_socket.setPos(*self.node.get_socket_position(index, position))
