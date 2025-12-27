"""
Scene
"""
import json
import logging
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, NotRequired, TypedDict

import typedload
from qtpy.QtWidgets import QGraphicsItem
from typedload.exceptions import TypedloadException

from qt_node_editor.node_edge import Edge, EdgeSerialize
from qt_node_editor.node_graphics_scene import QDMGraphicsScene
from qt_node_editor.node_node import Node, NodeSerialize
from qt_node_editor.node_scene_clipboard import SceneClipboard
from qt_node_editor.node_scene_history import SceneHistory
from qt_node_editor.node_serializable import Serializable, SerializableID

log = logging.getLogger(__name__)

class InvalidSceneFileError(Exception):
    "Invalid scene file."

class SceneSerialize(TypedDict):
    id: NotRequired[SerializableID]  # TODO: required
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
        self.last_selected_items = []

        # initialize all listeners
        self._has_been_modified_listeners: list[Callable[[], None]] = []
        self._item_selected_listeners: list[Callable[[], None]] = []
        self._items_deselected_listeners: list[Callable[[], None]] = []

        self.init_ui()
        self.history = SceneHistory(self)
        self.clipboard = SceneClipboard(self)

        # self.gr_scene.item_selected.connect(self.on_item_selected)
        # self.gr_scene.items_deselected.connect(self.on_items_deselected)
        self.gr_scene.selectionChanged.connect(self.on_selection_changed)
        self._selection_handling = True

    def init_ui(self):
        self.gr_scene = QDMGraphicsScene(self)
        self.gr_scene.set_rect(self.scene_width, self.scene_height)

    # def on_item_selected(self) -> None:
    #     print("SCENE:: ~on_item_selected")
    #     current_selected_items = self.get_selected_items()
    #     if current_selected_items != self.last_selected_items:
    #         print(current_selected_items)
    #         self.last_selected_items = current_selected_items
    #         self.history.store_history("Selection Changed")
    #         for callback in self._item_selected_listeners:
    #             callback()

    # def on_items_deselected(self) -> None:
    #     print("SCENE:: ~on_item_deselected")
    #     self.reset_last_selected_states()
    #     print(self.last_selected_items)
    #     if self.last_selected_items:
    #         self.last_selected_items = []
    #         self.history.store_history("Deselected everything")
    #         for callback in self._items_deselected_listeners:
    #             callback()

    def on_selection_changed(self) -> None:
        "Handle selection changes on the scene."
        if not self._selection_handling:
            return
        if current_selected_items := self.get_selected_items():
            if current_selected_items != self.last_selected_items:
                self.last_selected_items = current_selected_items
                self.history.store_history("Selection Changed", modified=False)
                for callback in self._item_selected_listeners:
                    callback()
        elif self.last_selected_items:
            self.last_selected_items = []
            self.history.store_history("Deselected everything", modified=False)
            for callback in self._items_deselected_listeners:
                callback()

    def set_selection_handling(self, *, enable: bool) -> None:
        "Enable or disable handling of selection changes on the scene."
        self._selection_handling = enable

    @contextmanager
    def selection_handling_disabled(self) -> Generator[None, Any, Any]:
        "Temporary disable handling of selection changes on the scene."
        self._selection_handling = False
        yield
        self._selection_handling = True

    def get_selected_items(self) -> list[QGraphicsItem]:
        "Get a list of selected elements on the scene."
        return self.gr_scene.selectedItems()

    @property
    def has_been_modified(self) -> bool:
        "Check if the scene is modified."
        return self._has_been_modified

    @has_been_modified.setter
    def has_been_modified(self, value: bool) -> None:
        # TODO: modified -> unmodified: callbacks are not called
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

    def rem_has_been_modified_listener(self, callback: Callable[[], None]) -> None:
        """
        Remove a previously added callback for the scene modification.

        :param callback: A callback function
        :type callback: Callable[[], None]
        """
        self._has_been_modified_listeners.remove(callback)

    def add_item_selected_listener(self, callback: Callable[[], None]) -> None:
        """
        Add a new callback to be called when an item is selected on the scene.

        :param callback: A callback function
        :type callback: Callable[[], None]
        """
        self._item_selected_listeners.append(callback)

    def add_items_deselected_listener(self, callback: Callable[[], None]) -> None:
        """
        Add a new callback to be called when items are deselected on the scene.

        :param callback: A callback function
        :type callback: Callable[[], None]
        """
        self._items_deselected_listeners.append(callback)

    # # custom flag to detect node or edge has been selected....
    # def reset_last_selected_states(self) -> None:
    #     for node in self.nodes:
    #         node.gr_node._last_selected_state = False
    #     for edge in self.edges:
    #         edge.gr_edge._last_selected_state = False

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
