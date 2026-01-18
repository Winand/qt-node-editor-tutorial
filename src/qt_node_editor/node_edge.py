"Module contains class for representing an Edge between nodes."
import logging
from enum import Enum, auto
from typing import TYPE_CHECKING, TypedDict, cast, override

from qt_node_editor.node_graphics_edge import (
    QDMGraphicsEdgeBezier,
    QDMGraphicsEdgeDirect,
)
from qt_node_editor.node_node import Node
from qt_node_editor.node_serializable import (
    Serializable,
    SerializableID,
    SerializableMap,
)
from qt_node_editor.node_socket import Socket

if TYPE_CHECKING:
    from qt_node_editor.node_scene import Scene


class EdgeType(int, Enum):
    "Edge visual appearance."
    DIRECT = auto()  #: see :class:`.QDMGraphicsEdgeDirect`
    BEZIER = auto()  #: see :class:`.QDMGraphicsEdgeBezier`

class EdgeSerialize(TypedDict):
    "Serialized edge data structure."
    id: SerializableID
    edge_type: EdgeType
    start: SerializableID | None
    end: SerializableID | None

log = logging.getLogger(__name__)


class Edge(Serializable):
    "Class for representing Edge in node editor."

    # TODO: start_socket can be None?
    def __init__(self, scene: "Scene", start_socket: Socket | None = None,
                 end_socket: Socket | None = None, shape: EdgeType = EdgeType.DIRECT,
                 ) -> None:
        """Initialize :class:`Edge`.

        :param scene: Reference to a :class:`.Scene` instance
        :type scene: Scene
        :param start_socket: Reference to the starting socket
        :type start_socket: Socket | None
        :param end_socket: Reference to the end socket or ``None``
        :type end_socket: Socket | None
        :param shape: Edge shape
        :type shape: EdgeType
        """
        super().__init__()
        self.scene = scene  #: Reference to a :class:`.Scene` instance

        # default init
        self._start_socket = None
        self._end_socket = None

        self.start_socket = start_socket
        self.end_socket = end_socket
        self.edge_type = shape

        self.scene.add_edge(self)

    def __str__(self) -> str:
        start_sock = hex(id(self.start_socket))[-3:] if self.start_socket else None
        end_sock = hex(id(self.end_socket))[-3:] if self.end_socket else None
        return (f"<Edge ..{hex(id(self))[-5:]} "
                f"(sockets {start_sock} <--> {end_sock})>")

    @property
    def start_socket(self) -> Socket | None:
        """
        Start socket to which the edge is connected.

        :getter: Returns start :class:`.Socket` or ``None``
        :setter: Sets start :class:`.Socket` safely
        """
        return self._start_socket

    @start_socket.setter
    def start_socket(self, value: Socket | None) -> None:
        if self.start_socket:  # delete this edge from the previous socket
            self.start_socket.remove_edge(self)
        self._start_socket = value
        if self.start_socket is not None:
            self.start_socket.add_edge(self)

    @property
    def end_socket(self) -> Socket | None:
        """
        End socket to which the edge is connected.

        :getter: Returns end :class:`.Socket` or ``None``
        :setter: Sets end :class:`.Socket` safely
        """
        return self._end_socket

    @end_socket.setter
    def end_socket(self, value: Socket | None) -> None:
        if self.end_socket:  # delete this edge from the previous socket
            self.end_socket.remove_edge(self)
        self._end_socket = value
        if self.end_socket is not None:
            self.end_socket.add_edge(self)

    @property
    def edge_type(self) -> EdgeType:
        """
        Edge type. See :class:`EdgeType`.

        :getter: get edge type constant for current ``Edge``
        :getter: sets new edge type. On background creates new :class:`.QDMGraphicsEdge`
        """
        return self._edge_type

    @edge_type.setter
    def edge_type(self, value: EdgeType) -> None:
        if hasattr(self, "gr_edge") and self.gr_edge is not None:
            self.scene.gr_scene.removeItem(self.gr_edge)

        self._edge_type = value
        if self._edge_type == EdgeType.DIRECT:
            self.gr_edge = QDMGraphicsEdgeDirect(self)
        elif self._edge_type == EdgeType.BEZIER:
            self.gr_edge = QDMGraphicsEdgeBezier(self)
        else:
            msg = f"Unknown edge type: {value}"
            raise ValueError(msg)

        self.scene.gr_scene.addItem(self.gr_edge)
        if self.start_socket is not None:
            self.update_positions()

    def get_connected_node(self, socket: Socket) -> Node | None:
        """
        Get a node on the other end of the edge.

        :param socket: A known :class:`.Socket` to determine the opposite one
        :return: A node to which the opposite socket belongs or ``None``
        """
        if other_socket := self.start_socket if socket == self.end_socket else \
                           self.end_socket:
            return other_socket.node
        return None

    def update_positions(self) -> None:
        "Update start and end points of the edge on a scene."
        if not self.start_socket or not self.gr_edge:
            # @Winand
            # disconnect_from_sockets sets start_socket to None
            # remove sets gr_edge to None
            msg = f"{self.start_socket=} {self.gr_edge=}"
            raise ValueError(msg)
        source_pos = list(self.start_socket.get_socket_position())
        source_pos[0] += self.start_socket.node.gr_node.pos().x()
        source_pos[1] += self.start_socket.node.gr_node.pos().y()
        self.gr_edge.set_source(*source_pos)
        if self.end_socket is not None:
            end_pos = list(self.end_socket.get_socket_position())
            end_pos[0] += self.end_socket.node.gr_node.pos().x()
            end_pos[1] += self.end_socket.node.gr_node.pos().y()
            self.gr_edge.set_destination(*end_pos)
        else:  # dragging mode
            self.gr_edge.set_destination(*source_pos)

    def disconnect_from_sockets(self) -> None:
        "Reset start and end sockets to ``None``."
        # TODO: Fix me!!!
        # if self.start_socket is not None:
        #     self.start_socket.remove_edge(self)
        # if self.end_socket is not None:
        #     self.end_socket.remove_edge(self)
        self.end_socket = None
        self.start_socket = None

    def remove(self) -> None:
        """
        Safely remove the edge from the scene.

        Notifies previously connected sockets about connection and input change.
        Triggers node methods:

        - :meth:`.Node.on_edge_connection_changed`
        - :meth:`.Node.on_input_data_changed`
        """
        old_start_socket, old_end_socket = self.start_socket, self.end_socket
        log.debug("# Removing Edge %s", self)
        log.debug(" - remove edge from all sockets")
        self.disconnect_from_sockets()
        log.debug(" - remove gr_edge")
        self.scene.gr_scene.removeItem(self.gr_edge)  # TODO: move to Scene.remove_edge?
        del self.gr_edge  # TODO: is reference removal required?
        log.debug(" - remove edge from scene")
        try:
            self.scene.remove_edge(self)
        except ValueError:
            log.exception("Remove edge")  # FIXME: eliminate exception handling here
        log.debug(" - everything is done.")

        if old_start_socket and old_end_socket:  # WA: connected edge (not dragging)
            # notify nodes from old sockets
            for socket in (old_start_socket, old_end_socket):
                socket.node.on_edge_connection_changed(self)
                if socket.is_input:
                    socket.node.on_input_data_changed(self)

    @override
    def serialize(self) -> EdgeSerialize:
        return {
            "id": self.id,
            "edge_type": self.edge_type,
            "start": self.start_socket.id if self.start_socket else None,
            "end": self.end_socket.id if self.end_socket else None
        }

    @override
    def deserialize(self, data: EdgeSerialize, hashmap: SerializableMap, *,
                    restore_id: bool = True) -> bool:
        if restore_id:
            self.id = data["id"]
        assert data["start"]
        self.start_socket = cast(Socket, hashmap[data["start"]])
        assert data["end"]
        self.end_socket = cast(Socket, hashmap[data["end"]])
        self.edge_type = data["edge_type"]
        return True
