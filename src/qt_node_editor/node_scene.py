"""
Scene
"""
import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import NotRequired, TypedDict

import typedload
from qtpy.QtWidgets import QGraphicsItem
from typedload.exceptions import TypedloadException

from qt_node_editor.node_edge import Edge, EdgeSerialize
from qt_node_editor.node_graphics_scene import QDMGraphicsScene
from qt_node_editor.node_node import Node, NodeSerialize
from qt_node_editor.node_scene_clipboard import SceneClipboard
from qt_node_editor.node_scene_history import SceneHistory
from qt_node_editor.node_serializable import Serializable

log = logging.getLogger(__name__)

class InvalidSceneFileError(Exception):
    "Invalid scene file."

class SceneSerialize(TypedDict):
    id: NotRequired[int]  # TODO: required
    width: NotRequired[int]  # TODO: required
    height: NotRequired[int]  # TODO: required
    nodes: list[NodeSerialize]
    edges: list[EdgeSerialize]

class Scene(Serializable):
    def __init__(self):
        super().__init__()
        self.nodes: list[Node] = []
        self.edges: list[Edge] = []

        self.scene_width = 64000
        self.scene_height = 64000

        self._has_been_modified = False
        self._has_been_modified_listeners: list[Callable[[], None]] = []

        self.init_ui()
        self.history = SceneHistory(self)
        self.clipboard = SceneClipboard(self)

    def get_selected_items(self) -> list[QGraphicsItem]:
        "Get a list of selected elements on the scene."
        return self.gr_scene.selectedItems()

    @property
    def has_been_modified(self) -> bool:
        "Check if the scene is modified."
        return self._has_been_modified

    @has_been_modified.setter
    def has_been_modified(self, value: bool) -> None:
        if not self._has_been_modified and value:
            self._has_been_modified = True
            for callback in self._has_been_modified_listeners:
                callback()
        self._has_been_modified = value

    def add_has_been_modified_listener(self, callback: Callable[[], None]) -> None:
        """
        Add a new callback to be called when the scene is modified.

        :param callback: A callback function
        :type callback: Callable[[], None]
        """
        self._has_been_modified_listeners.append(callback)

    def init_ui(self):
        self.gr_scene = QDMGraphicsScene(self)
        self.gr_scene.set_rect(self.scene_width, self.scene_height)

    def add_node(self, node: "Node"):
        self.nodes.append(node)

    def add_edge(self, edge: "Edge"):
        self.edges.append(edge)

    def remove_node(self, node: "Node"):
        if node in self.nodes:
            self.nodes.remove(node)
        else:
            log.warning("Node %s not found in the scene node list.", node)

    def remove_edge(self, edge: "Edge"):
        if edge in self.edges:
            self.edges.remove(edge)
        else:
            log.warning("Node %s not found in the scene edge list.", edge)

    def clear(self):
        "Clear the scene."
        while len(self.nodes) > 0:
            self.nodes[0].remove()
        self.has_been_modified = False
        # TODO: clear history here? see self.history.history_stack

    def save_to_file(self, filename: Path) -> None:
        "Save the scene to file."
        with filename.open("w", encoding="utf-8") as file:
            file.write(json.dumps(self.serialize(), indent=4))
        self.has_been_modified = False
        print(f"Saving to {filename} was successfull")

    def load_from_file(self, filename: Path) -> None:
        "Load scene from file."
        try:
            with filename.open(encoding="utf-8") as file:
                data = typedload.load(json.load(file), SceneSerialize)
        except json.JSONDecodeError as e:
            msg = f"{filename.name} is not a valid JSON file"
            raise InvalidSceneFileError(msg) from e
        except TypedloadException as e:
            msg = f"{filename.name} is not a valid scene file"
            raise InvalidSceneFileError(msg) from e
        self.deserialize(data)
        self.has_been_modified = False

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
