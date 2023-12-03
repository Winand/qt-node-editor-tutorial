"""
Edge between nodes
"""
import logging
from enum import Enum, auto
from typing import TYPE_CHECKING, TypedDict

from qt_node_editor.node_graphics_edge import (QDMGraphicsEdgeBezier,
                                               QDMGraphicsEdgeDirect)
from qt_node_editor.node_serializable import Serializable
from qt_node_editor.node_socket import Socket

if TYPE_CHECKING:
    from qt_node_editor.node_scene import Scene


class EdgeType(int, Enum):
    "Edge visual appearance"
    DIRECT = auto()
    BEZIER = auto()

class EdgeSerialize(TypedDict):
    id: int
    edge_type: EdgeType
    start: int | None
    end: int | None

log = logging.getLogger(__name__)


class Edge(Serializable):
    def __init__(self, scene: "Scene", start_socket: Socket | None=None,
                 end_socket: Socket | None = None, shape=EdgeType.DIRECT) -> None:
        super().__init__()
        self.scene = scene
        self.start_socket = start_socket
        self.end_socket = end_socket
        self.edge_type = shape

        self.scene.add_edge(self)

    def __str__(self):
        start_sock = hex(id(self.start_socket))[-3:] if self.start_socket else None
        end_sock = hex(id(self.end_socket))[-3:] if self.end_socket else None
        return (f"<Edge ..{hex(id(self))[-5:]} "
                f"(sockets {start_sock} <--> {end_sock})>")

    @property
    def start_socket(self) -> Socket | None:
        return self._start_socket

    @start_socket.setter
    def start_socket(self, value):
        self._start_socket = value
        if self.start_socket is not None:
            self.start_socket.edge = self

    @property
    def end_socket(self) -> Socket | None:
        return self._end_socket

    @end_socket.setter
    def end_socket(self, value):
        self._end_socket = value
        if self.end_socket is not None:
            self.end_socket.edge = self

    @property
    def edge_type(self) -> EdgeType:
        return self._edge_type

    @edge_type.setter
    def edge_type(self, value: EdgeType):
        if hasattr(self, "gr_edge") and self.gr_edge is not None:
            self.scene.gr_scene.removeItem(self.gr_edge)

        self._edge_type = value
        if self._edge_type == EdgeType.DIRECT:
            self.gr_edge = QDMGraphicsEdgeDirect(self)
        elif self._edge_type == EdgeType.BEZIER:
            self.gr_edge = QDMGraphicsEdgeBezier(self)
        else:
            raise ValueError(f"Unknown edge type: {value}")

        self.scene.gr_scene.addItem(self.gr_edge)
        if self.start_socket is not None:
            self.update_positions()

    def update_positions(self):
        "Update start and end points of the edge on a scene"
        if not self.start_socket or not self.gr_edge:
            # @Winand
            # disconnect_from_sockets sets start_socket to None
            # remove sets gr_edge to None
            raise ValueError(f"{self.start_socket=} {self.gr_edge=}")
        source_pos = self.start_socket.get_socket_position()
        source_pos[0] += self.start_socket.node.gr_node.pos().x()
        source_pos[1] += self.start_socket.node.gr_node.pos().y()
        self.gr_edge.set_source(*source_pos)
        if self.end_socket is not None:
            end_pos = self.end_socket.get_socket_position()
            end_pos[0] += self.end_socket.node.gr_node.pos().x()
            end_pos[1] += self.end_socket.node.gr_node.pos().y()
            self.gr_edge.set_destination(*end_pos)
        else:  # dragging mode
            self.gr_edge.set_destination(*source_pos)
        self.gr_edge.update()

    def disconnect_from_sockets(self):
        if self.start_socket is not None:
            self.start_socket.edge = None
        if self.end_socket is not None:
            self.end_socket.edge = None
        self.end_socket = None
        self.start_socket = None

    def remove(self):
        log.debug("# Removing Edge %s", self)
        log.debug(" - remove edge from all sockets")
        self.disconnect_from_sockets()
        log.debug(" - remove gr_edge")
        self.scene.gr_scene.removeItem(self.gr_edge)  # TODO: move to Scene.remove_edge?
        self.gr_edge = None
        log.debug(" - remove edge from scene")
        try:
            self.scene.remove_edge(self)
        except ValueError:
            pass  # FIXME: eliminate exception handling here
        log.debug(" - everything is done.")

    def serialize(self) -> EdgeSerialize:
        return {
            "id": self.id,
            "edge_type": self.edge_type,
            "start": self.start_socket.id if self.start_socket else None,
            "end": self.end_socket.id if self.end_socket else None
        }

    def deserialize(self, data: EdgeSerialize, hashmap: dict = {},
                    restore_id=True):
        if restore_id:
            self.id = data["id"]
        self.start_socket = hashmap[data["start"]]
        self.end_socket = hashmap[data["end"]]
        self.edge_type = data["edge_type"]
        return True
