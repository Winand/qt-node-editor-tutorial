"""
Edge between nodes
"""
from enum import Enum, auto

from qt_node_editor.node_graphics_edge import (QDMGraphicsEdgeBezier,
                                               QDMGraphicsEdgeDirect)
from qt_node_editor.node_scene import Scene
from qt_node_editor.node_socket import Socket


class EdgeType(Enum):
    "Edge visual appearance"
    Direct = auto()
    Bezier = auto()


class Edge:
    def __init__(self, scene: Scene, start_socket: Socket, end_socket: Socket,
                 shape=EdgeType.Direct) -> None:
        self.scene = scene
        self.start_socket = start_socket
        self.end_socket = end_socket

        if shape == EdgeType.Direct:
            self.gr_edge = QDMGraphicsEdgeDirect(self)
        elif shape == EdgeType.Bezier:
            self.gr_edge = QDMGraphicsEdgeBezier(self)
        self.update_positions()
        # print(f"Edge: {self.gr_edge.pos_source} to {self.gr_edge.pos_destination}")
        self.scene.gr_scene.addItem(self.gr_edge)

    def update_positions(self):
        "Update start and end points of the edge on a scene"
        if not self.start_socket or not self.gr_edge:
            # @Winand
            # disconnect_from_sockets sets start_socket to None
            # remove sets gr_edge to None
            raise ValueError
        source_pos = self.start_socket.get_socket_position()
        source_pos[0] += self.start_socket.node.gr_node.pos().x()
        source_pos[1] += self.start_socket.node.gr_node.pos().y()
        self.gr_edge.set_source(*source_pos)
        if self.end_socket is not None:
            end_pos = self.end_socket.get_socket_position()
            end_pos[0] += self.end_socket.node.gr_node.pos().x()
            end_pos[1] += self.end_socket.node.gr_node.pos().y()
            self.gr_edge.set_destination(*end_pos)
        self.gr_edge.update()

    def disconnect_from_sockets(self):
        if self.start_socket is not None:
            self.start_socket.edge = None
        if self.end_socket is not None:
            self.end_socket.edge = None
        self.end_socket = None
        self.start_socket = None

    def remove(self):
        self.disconnect_from_sockets()
        self.scene.gr_scene.removeItem(self.gr_edge)  # TODO: move to Scene.remove_edge?
        self.gr_edge = None
        self.scene.remove_edge(self)
