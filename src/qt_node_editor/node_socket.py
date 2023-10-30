"""
Socket
"""
from enum import Enum, auto
from typing import TYPE_CHECKING

from qt_node_editor.node_graphics_socket import QDMGraphicsSocket

if TYPE_CHECKING:
    from qt_node_editor.node_edge import Edge
    from qt_node_editor.node_node import Node


class POS(Enum):
    LEFT_TOP = auto()
    LEFT_BOTTOM = auto()
    RIGHT_TOP = auto()
    RIGHT_BOTTOM = auto()


class Socket():
    def __init__(self, node: "Node", index = 0, position=POS.LEFT_TOP,
                 socket_type=1) -> None:
        self.node = node
        self.index = index
        self.position = position
        self.socket_type = socket_type

        self.gr_socket = QDMGraphicsSocket(node.gr_node, socket_type)
        self.gr_socket.setPos(*self.node.get_socket_position(index, position))

        self.edge = None

    def get_socket_position(self):
        return self.node.get_socket_position(self.index, self.position)

    def set_connected_edge(self, edge: "Edge"):
        self.edge = edge

    def has_edge(self):
        "Check if an edge is connected to the socket."
        return self.edge is not None
