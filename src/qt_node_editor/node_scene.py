"""
Scene
"""
import json
from typing import TypedDict

from qt_node_editor.node_edge import Edge, EdgeSerialize
from qt_node_editor.node_graphics_scene import QDMGraphicsScene
from qt_node_editor.node_node import Node, NodeSerialize
from qt_node_editor.node_scene_history import SceneHistory
from qt_node_editor.node_serializable import Serializable
from qt_node_editor.node_scene_clipboard import SceneClipboard

class SceneSerialize(TypedDict):
    id: int
    width: int
    height: int
    nodes: list[NodeSerialize]
    edges: list[EdgeSerialize]

class Scene(Serializable):
    def __init__(self):
        super().__init__()
        self.nodes: list[Node] = []
        self.edges: list[Edge] = []

        self.scene_width = 64000
        self.scene_height = 64000

        self.init_ui()
        self.history = SceneHistory(self)
        self.clipboard = SceneClipboard(self)

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

    def clear(self):
        "Clear the scene."
        while len(self.nodes) > 0:
            self.nodes[0].remove()

    def save_to_file(self, filename: str):
        "Save the scene to file."
        with open(filename, "w", encoding="utf-8") as file:
            file.write(json.dumps(self.serialize(), indent=4))
        print(f"Saving to {filename} was successfull")
    
    def load_from_file(self, filename: str):
        "Load scene from file."
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
            self.deserialize(data)

    def serialize(self) -> SceneSerialize:
        nodes = [n.serialize() for n in self.nodes]
        edges = [e.serialize() for e in self.edges]
        return {  # dicts are ordered in Python 3.7+
            "id": self.id,
            "width": self.scene_width,
            "height": self.scene_height,
            "nodes": nodes,
            "edges": edges
        }

    def deserialize(self, data: SceneSerialize, hashmap: dict | None = None,
                    restore_id=True):
        self.clear()
        hashmap = {}
        if restore_id:  # avoid id collisions when copying items
            self.id = data["id"]

        for node_data in data["nodes"]:
            Node(self).deserialize(node_data, hashmap, restore_id)

        for edge_data in data["edges"]:
            Edge(self).deserialize(edge_data, hashmap, restore_id)

        return True
