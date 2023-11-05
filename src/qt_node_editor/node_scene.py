"""
Scene
"""
from typing import TYPE_CHECKING

from .node_graphics_scene import QDMGraphicsScene

if TYPE_CHECKING:
    from qt_node_editor.node_edge import Edge
    from qt_node_editor.node_node import Node


class Scene:
    def __init__(self):
        self.nodes: list[Node] = []
        self.edges: list[Edge] = []

        self.scene_width = 64000
        self.scene_height = 64000

        self.init_ui()

    def init_ui(self):
        self.gr_scene = QDMGraphicsScene(self)
        self.gr_scene.set_rect(self.scene_width, self.scene_height)

    def add_node(self, node: "Node"):
        self.nodes.append(node)

    def add_edge(self, edge: "Edge"):
        self.edges.append(edge)

    def remove_node(self, node: "Node"):
        self.nodes.remove(node)

    def remove_edge(self, edge: "Edge"):
        self.edges.remove(edge)
