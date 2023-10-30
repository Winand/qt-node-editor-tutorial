from enum import Enum, auto

from qt_node_editor.node_graphics_edge import (QDMGraphicsEdgeBezier,
                                               QDMGraphicsEdgeDirect)


class EdgeType(Enum):
    "Edge visual appearance"
    Direct = auto()
    Bezier = auto()


class Edge:
    def __init__(self, scene, start_socket, end_socket,
                 shape=EdgeType.Direct) -> None:
        self.scene = scene
        self.start_socket = start_socket
        self.end_socket = end_socket

        if shape == EdgeType.Direct:
            self.gr_edge = QDMGraphicsEdgeDirect(self)
        elif shape == EdgeType.Bezier:
            self.gr_edge = QDMGraphicsEdgeBezier(self)
        self.scene.gr_scene.addItem(self.gr_edge)
