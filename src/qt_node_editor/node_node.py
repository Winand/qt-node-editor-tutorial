"Module for the default node implementation."
import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, NotRequired, TypedDict, overload, override

from qtpy.QtCore import QPointF

from qt_node_editor.node_content_widget import ContentSerialize, QDMContentWidget
from qt_node_editor.node_graphics_node import QDMGraphicsNode
from qt_node_editor.node_serializable import (
    Serializable,
    SerializableID,
    SerializableMap,
)
from qt_node_editor.node_socket import Pos, Socket, SocketSerialize
from qt_node_editor.utils import Size

if TYPE_CHECKING:
    from qt_node_editor.node_edge import Edge
    from qt_node_editor.node_scene import Scene

log = logging.getLogger(__name__)

class NodeSerialize(TypedDict):
    "Serialized node data structure."
    id: SerializableID  #: id of a node
    title: str  #: node title
    pos_x: float  #: node X position on the scene
    pos_y: float  #: node Y position on the scene
    width: NotRequired[float]
    """
    node width

    .. note:: ;TODO: not serialized yet
    """
    height: NotRequired[float]
    """
    node height

    .. note:: ;TODO: not serialized yet
    """
    inputs: list[SocketSerialize]  #: input sockets of the node
    outputs: list[SocketSerialize]  #: output sockets of the node
    content: ContentSerialize  #: node content serialized


class Node(Serializable):
    "Default node implementation."
    GraphicsNodeType = QDMGraphicsNode  #: graphical implementation used by this node
    content: QDMContentWidget

    def __init__(self, scene: "Scene", title: str = "Undefined Node",
                 inputs: list[int] | None = None,
                 outputs: list[int] | None = None) -> None:
        """
        Initialize a :class:`Node`.

        :param scene: reference to a :class:`.Scene`
        :param title: a title shown on the node
        :param inputs: list of input :class:`.Socket` types (colors)
        :param outputs: list of output :class:`.Socket` types (colors)
        """
        super().__init__()
        self._title = title  # FIXME: title is used from within QDMGraphicsNode constructor
        self.scene = scene  #: reference to a :class:`.Scene`
        self.init_gui_objects()
        self.init_settings()
        self.title = title

        self.scene.add_node(self)
        self.scene.gr_scene.addItem(self.gr_node)

        self.inputs: list[Socket] = []  #: list of input :class:`.Socket` objects
        self.outputs: list[Socket] = []  #: list of output :class:`.Socket` objects
        self._init_sockets(inputs, outputs)

        # dirty and evaluation
        self._is_dirty = False
        self._is_invalid = False

    def __str__(self):
        return f"<Node ..{hex(id(self))[-5:]} '{self.title}'>"

    @property
    def title(self) -> str:
        "Set text in node header area."
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = value
        self.gr_node.title = value

    @property
    def pos(self) -> QPointF:
        "Node position in a scene."
        return self.gr_node.pos()

    @overload
    def set_pos(self, x: float, y: float) -> None: ...
    @overload
    def set_pos(self, x: QPointF) -> None: ...
    def set_pos(self, x: float | QPointF, y: float | None = None) -> None:
        """
        Set node position on a scene.

        :param x: node X-coordinate or `QPointF` with `(x,y)` coordinates
        :param y: node Y-coordinate
        """
        if isinstance(x, QPointF):
            self.gr_node.setPos(x)
        elif y is not None:
            self.gr_node.setPos(x, y)
        else:
            raise TypeError

    def init_gui_objects(self) -> None:
        "Set up graphics node instance and content widget."
        #: instance of :class:`.QDMContentWidget` which is a container
        #: for the widgets inside of the node
        self.content = QDMContentWidget(self)
        self.gr_node = self.GraphicsNodeType(self)

    def init_settings(self) -> None:
        "Initialize node properties and socket options."
        self.socket_spacing = 22
        self.input_socket_position = Pos.LEFT_BOTTOM
        self.output_socket_position = Pos.RIGHT_TOP
        self.input_multi_edged = False
        self.output_multi_edged = True

    def _init_sockets(self, inputs: list[int] | None, outputs: list[int] | None,
                     *, reset: bool = True) -> None:
        "Create sockets for inputs and outputs, by default remove old sockets."
        if reset:  # clear sockets
            for socket in self.inputs + self.outputs:
                self.scene.gr_scene.removeItem(socket.gr_socket)
            self.inputs = []
            self.outputs = []

        inputs, outputs = inputs or [], outputs or []
        for index, socket_type in enumerate(inputs):
            socket = Socket(self, index, self.input_socket_position,
                            socket_type, multi_edges=self.input_multi_edged,
                            socket_count_on_side=len(inputs), is_input=True)
            self.inputs.append(socket)
        for index, socket_type in enumerate(outputs):
            socket = Socket(self, index, self.output_socket_position,
                            socket_type, multi_edges=self.output_multi_edged,
                            socket_count_on_side=len(outputs), is_input=False)
            self.outputs.append(socket)

    def on_edge_connection_changed(self, edge: "Edge") -> None:
        "Handle ``edge`` connection change."
        log.info("%s::on_edge_connection_changed: %s", self.__class__.__name__, edge)

    def on_input_data_changed(self, edge: "Edge") -> None:
        """
        Handle input connection change or input user data change.

        The node and its descendants are marked as "dirty".
        """
        log.info("%s::on_input_data_changed: %s", self.__class__.__name__, edge)
        self.mark_dirty()
        self.mark_descendants_dirty()

    def get_socket_position(self, index: int, position: Pos,
                            socket_count_on_side: int = 1) -> tuple[float, float]:
        """
        Get socket element `x,y` position by its index.

        This is used for placing graphics sockets on a graphics node.

        :param index: Order number of the Socket (zero based).
        :param position: Socket alignment on the node
        :param socket_count_on_side: Total number of Sockets at this :class:`.Pos`
        :return: `x,y` position of a socket on the node
        """
        x = 0 if position in (Pos.LEFT_TOP, Pos.LEFT_CENTER, Pos.LEFT_BOTTOM) else \
            float(self.gr_node.width)
        if position in (Pos.LEFT_BOTTOM, Pos.RIGHT_BOTTOM):
            y = self.gr_node.height - self.gr_node.edge_roundness - \
                self.gr_node.socket_vertical_padding - index * self.socket_spacing
        elif position in (Pos.LEFT_CENTER, Pos.RIGHT_CENTER):
            title_height = self.gr_node.title_height
            content_height = self.gr_node.height - title_height
            sockets_height = (socket_count_on_side - 1) * self.socket_spacing
            sockets_top = (content_height - sockets_height) / 2
            y = title_height + sockets_top + index * self.socket_spacing
        elif position in (Pos.LEFT_TOP, Pos.RIGHT_TOP):
            y = self.gr_node.title_height + self.gr_node.socket_vertical_padding + \
                index * self.socket_spacing
        else:
            msg = f"Unknown socket position {position}"
            raise ValueError(msg)
        return (x, y)

    def update_connected_edges(self) -> None:
        "Update location of edges connected to the node."
        for socket in self.inputs + self.outputs:
            for edge in socket.edges:
                edge.update_positions()

    def remove(self) -> None:
        "Remove this node from the scene and clean up."
        log.debug("> Removing node %s", self)
        log.debug(" - remove all edges from sockets")
        for socket in (self.inputs + self.outputs):
            for edge in socket.edges:
                log.debug("    - removing from socket %s edge %s", socket, edge)
                edge.remove()
        log.debug(" - remove gr_node")
        self.scene.gr_scene.removeItem(self.gr_node)
        self.gr_node = None  # TODO: do not set to None as it confuses linters
        log.debug(" - remove node from the scene")
        self.scene.remove_node(self)
        log.debug(" - everything was done.")

    def is_dirty(self) -> bool:
        "Check if a node has dirty state."
        return self._is_dirty

    def mark_dirty(self, *, unset: bool = False) -> None:
        "Mark or unmark a node to have dirty state."
        self._is_dirty = not unset
        if self._is_dirty:
            self.on_marked_dirty()

    def on_marked_dirty(self) -> None:
        "Node has been marked as `dirty`. Can be overriden."

    def mark_children_dirty(self, *, unset: bool = False) -> None:
        "Mark or unmark children nodes to have dirty state."
        for node in self.get_children_nodes():
            node.mark_dirty(unset=unset)

    # https://www.youtube.com/watch?v=NgBhr2k5IJs&lc=UgzfobDHlvYrE4YZ2Td4AaABAg.98oD9yaLPE6A2AR5ddgHxY
    def mark_descendants_dirty(self, *, unset: bool = False) -> None:
        "Mark or unmark all descendant nodes to have dirty state."
        for node in self.get_children_nodes():
            node.mark_dirty(unset=unset)
            node.mark_descendants_dirty(unset=unset)

    def is_invalid(self) -> bool:
        "Check if a node has invalid state."
        return self._is_invalid

    def mark_invalid(self, *, unset: bool = False) -> None:
        "Mark or unmark a node to have invalid state."
        self._is_invalid = not unset
        if self._is_invalid:
            self.on_marked_invalid()

    def on_marked_invalid(self) -> None:
        "Node has been marked as `invalid`. Can be overriden."

    def mark_children_invalid(self, *, unset: bool = False) -> None:
        "Mark or unmark children nodes to have invalid state."
        for node in self.get_children_nodes():
            node.mark_invalid(unset=unset)

    # https://www.youtube.com/watch?v=NgBhr2k5IJs&lc=UgzfobDHlvYrE4YZ2Td4AaABAg.98oD9yaLPE6A2AR5ddgHxY
    # FIXME: how to address circular dependencies problem?
    def mark_descendants_invalid(self, *, unset: bool = False) -> None:
        "Mark or unmark all descendant nodes to have invalid state."
        for node in self.get_children_nodes():
            node.mark_invalid(unset=unset)
            node.mark_descendants_invalid(unset=unset)

    def eval(self) -> Any:  # noqa: ANN401
        "Evaluate node. Default implementation returns 0."
        self.mark_dirty(unset=True)
        self.mark_invalid(unset=True)
        return 0

    def eval_children(self) -> None:
        "Evaluate children nodes."
        for node in self.get_children_nodes():
            node.eval()

    def get_children_nodes(self) -> Iterable["Node"]:
        "Get nodes connected to the node outputs."
        return filter(None, (
            edge.get_connected_node(output)
            for output in self.outputs for edge in output.edges
        ))

    def get_input(self, index: int = 0) -> "Node | None":
        """
        Get the **first** :class:`Node` connected to the input with specified index.

        :param index: Order number of an input socket
        :return: A :class:`Node` or ``None`` if nothing is connected to the socket
        """
        socket = self.inputs[index]
        if not socket.edges:  # WA
            log.info("Cannot get input, none is attached to %s:%d", self.title, index)
            return None
        return socket.edges[0].get_connected_node(socket)

    def get_inputs(self, index: int = 0) -> list["Node"]:
        """
        Get all node objects connected to the input socket with specified index.

        :param index: Order number of an input socket
        :return: All :class:`Node` instances connected to the input socket
        """
        socket = self.inputs[index]
        return list(filter(None, (
            edge.get_connected_node(socket) for edge in socket.edges
        )))

    def get_outputs(self, index: int = 0) -> list["Node"]:
        """
        Get all node objects connected to the output socket with specified index.

        :param index: Order number of an output socket
        :return: All :class:`Node` instances connected to the output socket
        """
        socket = self.outputs[index]
        return list(filter(None, (
            edge.get_connected_node(socket) for edge in socket.edges
        )))

    @override
    def serialize(self) -> NodeSerialize:
        scene_pos = self.gr_node.scenePos()
        inputs = [i.serialize() for i in self.inputs]
        outputs = [o.serialize() for o in self.outputs]
        return {
            "id": self.id,
            "title": self.title,
            "pos_x":  scene_pos.x(),
            "pos_y":  scene_pos.y(),
            "inputs": inputs,
            "outputs": outputs,
            "content": self.content.serialize()
        }

    @property
    def size(self) -> Size:
        "Graphical node dimensions."
        return self.gr_node.size

    @override
    def deserialize(self, data: NodeSerialize, hashmap: SerializableMap, *,
                    restore_id: bool = True) -> bool:
        # FIXME: use some kind of a fixed structure instead of a dict?
        if restore_id:
            self.id = data["id"]
        hashmap[self.id] = self

        self.set_pos(data["pos_x"], data["pos_y"])
        self.title = data["title"]
        # FIXME: is it a good solution?
        data["inputs"].sort(key=lambda s: s["index"] + s["position"] * 10000)
        data["outputs"].sort(key=lambda s: s["index"] + s["position"] * 10000)

        self.inputs = []
        for socket_data in data["inputs"]:
            new_socket = Socket(node=self, index=socket_data["index"],
                                position=socket_data["position"],
                                socket_type=socket_data["socket_type"],
                                socket_count_on_side=len(data["inputs"]),
                                is_input=True)  # FIXME: multi_edges=False?
            new_socket.deserialize(socket_data, hashmap, restore_id=restore_id)
            self.inputs.append(new_socket)

        self.outputs = []
        for socket_data in data["outputs"]:
            new_socket = Socket(node=self, index=socket_data["index"],
                                position=socket_data["position"],
                                socket_type=socket_data["socket_type"],
                                socket_count_on_side=len(data["outputs"]),
                                is_input=False)
            new_socket.deserialize(socket_data, hashmap, restore_id=restore_id)
            self.outputs.append(new_socket)

        return self.content.deserialize(data["content"], hashmap)
