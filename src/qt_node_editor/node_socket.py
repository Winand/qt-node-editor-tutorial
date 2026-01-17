"Module for the :class:`Socket` class."
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
    "Socket alignment on a Node."
    LEFT_TOP = auto()
    LEFT_CENTER = auto()
    LEFT_BOTTOM = auto()
    RIGHT_TOP = auto()
    RIGHT_CENTER = auto()
    RIGHT_BOTTOM = auto()

class SocketSerialize(TypedDict):
    "Serialized socket data structure."
    id: SerializableID  #: ID of a socket
    index: int  #: Index of a socket in its position on the Node
    multi_edges: NotRequired[bool]  #: a socket can have multiple edges connected
    position: Pos  #: Alignment of a socket on a Node
    socket_type: int  #: Socket color index, see :data:`.SOCKET_COLORS`

log = logging.getLogger(__name__)


class Socket(Serializable):
    "Class representing a socket of a node."

    def __init__(self, node: "Node", index: int = 0, position: Pos = Pos.LEFT_TOP,
                 socket_type: int = 1, *, multi_edges: bool = True,
                 socket_count_on_side: int = 1, is_input: bool = False) -> None:
        """
        Initialize :class:`.Socket`.

        :param node: Reference to a :class:`.Node` object containing the socket
        :param index: Index of the socket in its position on a Node
        :param position: Alignment of the socket on a Node (left, right, top, bottom)
        :param socket_type: Socket color index, see :data:`.SOCKET_COLORS`
        :param multi_edges: ``True`` if the socket can have multiple edges connected
        :param socket_count_on_side: total number of sockets in this `position`
        :param is_input: ``True`` if it is an input socket
        """
        super().__init__()
        self.node = node  #: Reference to a :class:`.Node` object containing the socket
        self.position = position  #: Alignment of the socket on a Node
        self.index = index  #: Index of the socket in its position on a Node
        self.socket_type = socket_type  # Socket color index, see :data:`.SOCKET_COLORS`
        #: total number of sockets in this `position`
        self.socket_count_on_side = socket_count_on_side  # FIXME: handle in Node
        self.is_multi_edges = multi_edges  #: Socket can have multiple edges connected
        self.is_input = is_input  #: ``True`` if it is an input socket
        self.is_output = not is_input  #: ``True`` if it is an output socket

        self.gr_socket = QDMGraphicsSocket(self, socket_type)
        self.set_socket_position()

        self.edges: list[Edge] = []  #: Edges connected to the socket

    def __str__(self) -> str:
        multi = " multi" if self.is_multi_edges else ""
        return f"<Socket{multi} ..{hex(id(self))[-5:]} '{self.node.title}'>"

    def set_socket_position(self) -> None:
        "Set graphical socket (x, y) position."
        self.gr_socket.setPos(*self.get_socket_position())

    def get_socket_position(self) -> tuple[float, float]:
        """
        Get (x, y) position of the socket as a tuple.

        :return: Return the socket position as :class:`.Node` reports it.
        :rtype: tuple[float, float]
        """
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

    def _determine_multi_edges(self, data: SocketSerialize) -> bool:
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
    def deserialize(self, data: SocketSerialize, hashmap: SerializableMap, *,
                    restore_id: bool = True) -> bool:
        if restore_id:
            self.id = data["id"]
        self.is_multi_edges = self._determine_multi_edges(data)  # TODO: in __init__? https://youtu.be/sKzNjQb3eWA?t=268
        # NOTE: data["id"] is used even w/ restore_id=False
        # so edges can find the right sockets on copy
        hashmap[data["id"]] = self
        return True
