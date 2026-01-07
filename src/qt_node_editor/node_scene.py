"""
Scene
"""
import json
import logging
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    NotRequired,
    TypedDict,
    cast,
    get_type_hints,
    override,
)

from qtpy.QtCore import QPoint
from qtpy.QtGui import QDragEnterEvent, QDropEvent
from qtpy.QtWidgets import QGraphicsItem
from typedload.dataloader import Loader, _typeddictload
from typedload.exceptions import TypedloadException
from typedload.typechecks import is_typeddict

from qt_node_editor.node_content_widget import ContentSerialize
from qt_node_editor.node_edge import Edge, EdgeSerialize
from qt_node_editor.node_graphics_scene import QDMGraphicsScene
from qt_node_editor.node_node import Node, NodeSerialize
from qt_node_editor.node_scene_clipboard import SceneClipboard
from qt_node_editor.node_scene_history import SceneHistory
from qt_node_editor.node_serializable import (
    Serializable,
    SerializableID,
    SerializableMap,
)
from qt_node_editor.utils import ref

if TYPE_CHECKING:
    from weakref import ReferenceType

    from qt_node_editor.node_graphics_view import QDMGraphicsView

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
        self._has_been_modified_listeners: list[ReferenceType[Callable[[], None]]] = []
        self._item_selected_listeners: list[ReferenceType[Callable[[], None]]] = []
        self._items_deselected_listeners: list[ReferenceType[Callable[[], None]]] = []

        self.node_class_selector: Callable[[NodeSerialize], type[Node] | None] \
            = lambda _data: Node

        self.init_ui()
        self.init_validator()
        self.history = SceneHistory(self)
        self.clipboard = SceneClipboard(self)

        # self.gr_scene.item_selected.connect(self.on_item_selected)
        # self.gr_scene.items_deselected.connect(self.on_items_deselected)
        self.gr_scene.selectionChanged.connect(self.on_selection_changed)
        self._selection_handling = True

    def init_ui(self):
        self.gr_scene = QDMGraphicsScene(self)  # TODO: graphics scene has no parent
        self.gr_scene.set_rect(self.scene_width, self.scene_height)

    def init_validator(self) -> None:
        "Support custom node types using a custom handler and type hints."
        self.validator = Loader()
        last_node_type: type[Node]  # store node type to get right content type

        def node_handler(_loader: Loader, value: Any, _type: type) -> Any:
            try:
                if _type is NodeSerialize:
                    # get concrete structure from NodeSerialize.serialize return type
                    nonlocal last_node_type
                    last_node_type = self.get_node_type(value)
                    _type = get_type_hints(last_node_type.serialize)["return"]
                if _type is ContentSerialize:
                    # get concrete structure from NodeSerialize.content.serialize
                    content_type = get_type_hints(last_node_type)["content"]
                    _type = get_type_hints(content_type.serialize)["return"]
            except Exception as e:
                msg = f"Cannot get serializaton type for {value}"
                raise TypedloadException(msg) from e
            return _typeddictload(_loader, value, _type)

        self.validator.handlers[
            self.validator.handlers.index((is_typeddict, _typeddictload))
        ] = (is_typeddict, node_handler)

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
                for callback_ref in self._item_selected_listeners:
                    if callback := callback_ref():
                        callback()
        elif self.last_selected_items:
            self.last_selected_items = []
            self.history.store_history("Deselected everything", modified=False)
            for callback_ref in self._items_deselected_listeners:
                if callback := callback_ref():
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
        # NOTE: for modified -> unmodified state callbacks are also called
        if self._has_been_modified != value:
            self._has_been_modified = value
            for callback_ref in self._has_been_modified_listeners:
                if callback := callback_ref():
                    callback()

    def add_has_been_modified_listener(self, callback: Callable[[], None]) -> None:
        """
        Add a new callback to be called when the scene is modified.

        :param callback: A callback function
        :type callback: Callable[[], None]
        """
        self._has_been_modified_listeners.append(ref(callback))

    def add_item_selected_listener(self, callback: Callable[[], None]) -> None:
        """
        Add a new callback to be called when an item is selected on the scene.

        :param callback: A callback function
        :type callback: Callable[[], None]
        """
        self._item_selected_listeners.append(ref(callback))

    def add_items_deselected_listener(self, callback: Callable[[], None]) -> None:
        """
        Add a new callback to be called when items are deselected on the scene.

        :param callback: A callback function
        :type callback: Callable[[], None]
        """
        self._items_deselected_listeners.append(ref(callback))

    def add_drag_enter_listener(self, callback: Callable[[QDragEnterEvent], None],
                                ) -> None:
        self.get_view().add_drag_enter_listener(callback)

    def add_drop_listener(self, callback: Callable[[QDropEvent], None]) -> None:
        self.get_view().add_drop_listener(callback)

    # # custom flag to detect node or edge has been selected....
    # def reset_last_selected_states(self) -> None:
    #     for node in self.nodes:
    #         node.gr_node._last_selected_state = False
    #     for edge in self.edges:
    #         edge.gr_edge._last_selected_state = False

    def get_view(self) -> "QDMGraphicsView":  # TODO: support multiple views
        "Get first view of the graphics scene."
        return cast('QDMGraphicsView', self.gr_scene.views()[0])

    def get_item_at(self, pos: QPoint) -> QGraphicsItem | None:
        return self.get_view().itemAt(pos)

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
                data = self.validator.load(json.load(file), SceneSerialize)
        except json.JSONDecodeError as e:
            msg = f"{filename.name} is not a valid JSON file"
            raise InvalidSceneFileError(msg) from e
        except TypedloadException as e:
            msg = f"{filename.name} is not a valid scene file"
            raise InvalidSceneFileError(msg) from e
        self.deserialize(data)
        self.has_been_modified = False

    def set_node_class_selector(
            self, selector: Callable[[NodeSerialize], type[Node] | None]) -> None:
        "Set node class retrieval function from serialized data. Default: data -> Node."
        self.node_class_selector = selector

    def get_node_type(self, data: NodeSerialize) -> type[Node]:
        "Retrieve node class from serialized node. Default: Node."
        return self.node_class_selector(data) or Node

    @override
    def serialize(self) -> SceneSerialize:
        nodes = [n.serialize() for n in self.nodes]
        edges = [e.serialize() for e in self.edges if e.end_socket]  # WA: not dragging
        return {  # dicts are ordered in Python 3.7+
            "id": self.id,
            "width": self.scene_width,
            "height": self.scene_height,
            "nodes": nodes,
            "edges": edges
        }

    @override
    def deserialize(self, data: SceneSerialize, hashmap: SerializableMap | None = None,
                    restore_id: bool = True) -> bool:
        self.clear()
        hashmap = {}
        if restore_id:  # avoid id collisions when copying items
            self.id = data["id"]

        for node_data in data["nodes"]:
            node_type = self.get_node_type(node_data)
            node_type(self).deserialize(node_data, hashmap, restore_id)

        for edge_data in data["edges"]:
            Edge(self).deserialize(edge_data, hashmap, restore_id)

        return True

    def __del__(self) -> None:
        log.debug("delete scene")
