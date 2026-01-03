"""
Socket
"""
import logging
from enum import Enum, auto
from typing import TYPE_CHECKING, NotRequired, TypedDict, override

from qt_node_editor.node_graphics_socket import QDMGraphicsSocket
from qt_node_editor.node_serializable import (
    Serializable,
    SerializableID,
    SerializableMap,
)

if TYPE_CHECKING:
    from qt_node_editor.node_edge import Edge
    from qt_node_editor.node_node import Node


# int required for serialization https://stackoverflow.com/q/24481852
class Pos(int, Enum):
    LEFT_TOP = auto()
    LEFT_CENTER = auto()
    LEFT_BOTTOM = auto()
    RIGHT_TOP = auto()
    RIGHT_CENTER = auto()
    RIGHT_BOTTOM = auto()

class SocketSerialize(TypedDict):
    id: SerializableID
    index: int
    multi_edges: NotRequired[bool]
    position: Pos
    socket_type: int

log = logging.getLogger(__name__)


class Socket(Serializable):
    def __init__(self, node: "Node", index = 0, position=Pos.LEFT_TOP,
                 socket_type=1, *, multi_edges: bool = True,
                 socket_count_on_side: int = 1, is_input: bool = False) -> None:
        super().__init__()
        self.node = node
        self.index = index
        self.position = position
        self.socket_type = socket_type
        self.is_multi_edges = multi_edges
        self.socket_count_on_side = socket_count_on_side  # FIXME: handle in Node
        self.is_input = is_input
        self.is_output = not is_input

        self.gr_socket = QDMGraphicsSocket(self, socket_type)
        self.set_socket_position()

        self.edges: list[Edge] = []

    def __str__(self):
        multi = " multi" if self.is_multi_edges else ""
        return f"<Socket{multi} ..{hex(id(self))[-5:]} '{self.node.title}'>"

    def set_socket_position(self) -> None:
        "Set graphical socket (x, y) position."
        self.gr_socket.setPos(*self.get_socket_position())

    def get_socket_position(self) -> tuple[float, float]:
        "Get (x, y) position of the socket as a tuple."
        return self.node.get_socket_position(self.index, self.position,
                                             self.socket_count_on_side)

    def add_edge(self, edge: "Edge") -> None:
        "Append a new edge to the edges connected to the socket."
        self.edges.append(edge)

    def remove_edge(self, edge: "Edge") -> None:
        "Remove an edge from the edges connected to the socket."
        if edge in self.edges:
            self.edges.remove(edge)
        else:
            log.warning("Edge %s not found in the socket's edge list.", edge)

    def remove_all_edges(self) -> None:
        "Remove all connected edges from the socket."
        while self.edges:
            self.edges.pop().remove()

    # def has_edge(self):
    #     "Check if an edge is connected to the socket."
    #     return self.edges is not None

    def determine_multi_edges(self, data: SocketSerialize) -> bool:
        "Get multi_edges property from data, by default return True for right sockets."
        return data.get(
            "multi_edges", data["position"] in { Pos.RIGHT_TOP, Pos.RIGHT_CENTER,
                                                 Pos.RIGHT_BOTTOM },
        )


    @override
    def serialize(self) -> SocketSerialize:
        return {
            "id": self.id,
            "index": self.index,
            "multi_edges": self.is_multi_edges,
            "position": self.position,
            "socket_type": self.socket_type,
        }

    @override
    def deserialize(self, data: SocketSerialize, hashmap: SerializableMap,
                    restore_id: bool = True) -> bool:
        if restore_id:
            self.id = data["id"]
        self.is_multi_edges = self.determine_multi_edges(data)  # TODO: in __init__? https://youtu.be/sKzNjQb3eWA?t=268
        # NOTE: data["id"] is used even w/ restore_id=False
        # so edges can find the right sockets on copy
        hashmap[data["id"]] = self
        return True
