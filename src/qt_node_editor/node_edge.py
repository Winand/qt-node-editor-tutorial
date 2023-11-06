"""
Edge between nodes
"""
import logging
from enum import Enum, auto

from qt_node_editor.node_graphics_edge import (QDMGraphicsEdgeBezier,
                                               QDMGraphicsEdgeDirect)
from qt_node_editor.node_scene import Scene
from qt_node_editor.node_serializable import Serializable
from qt_node_editor.node_socket import Socket


class EdgeType(int, Enum):
    "Edge visual appearance"
    DIRECT = auto()
    BEZIER = auto()

log = logging.getLogger(__name__)


class Edge(Serializable):
    def __init__(self, scene: Scene, start_socket: Socket, end_socket: Socket | None,
                 shape=EdgeType.DIRECT) -> None:
        super().__init__()
        self.scene = scene
        self.start_socket = start_socket
        self.end_socket = end_socket
        self.edge_type = shape
        self.start_socket.edge = self
        if self.end_socket is not None:
            self.end_socket.edge = self

        if shape == EdgeType.DIRECT:
            self.gr_edge = QDMGraphicsEdgeDirect(self)
        elif shape == EdgeType.BEZIER:
            self.gr_edge = QDMGraphicsEdgeBezier(self)
        else:
            raise ValueError(f"Unknown edge type: {shape}")
        self.update_positions()
        self.scene.gr_scene.addItem(self.gr_edge)
        self.scene.add_edge(self)

    def __str__(self):
        start_sock = hex(id(self.start_socket))[-3:] if self.start_socket else None
        end_sock = hex(id(self.end_socket))[-3:] if self.end_socket else None
        return (f"<Edge ..{hex(id(self))[-5:]} "
                f"(sockets {start_sock} <--> {end_sock})>")

    def update_positions(self):
        "Update start and end points of the edge on a scene"
        if not self.start_socket or not self.gr_edge:
            # @Winand
            # disconnect_from_sockets sets start_socket to None
            # remove sets gr_edge to None
            # FIXME: raises after two clicks on the same socket
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
    
    def serialize(self):
        return {
            "id": self.id,
            "edge_type": self.edge_type,
            "start": self.start_socket.id,
            "end": self.end_socket.id
        }

    def deserialize(self, data, hashmap: dict = {}):
        return False
