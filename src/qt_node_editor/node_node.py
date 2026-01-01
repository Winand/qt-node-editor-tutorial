"""
Node
"""
import logging
from typing import TYPE_CHECKING, TypedDict

from qt_node_editor.node_content_widget import ContentSerialize, QDMContentWidget
from qt_node_editor.node_graphics_node import QDMGraphicsNode
from qt_node_editor.node_serializable import Serializable, SerializableID
from qt_node_editor.node_socket import Pos, Socket, SocketSerialize

if TYPE_CHECKING:
    from qt_node_editor.node_scene import Scene

log = logging.getLogger(__name__)

class NodeSerialize(TypedDict):
    id: SerializableID
    title: str
    pos_x: float
    pos_y: float
    inputs: list[SocketSerialize]
    outputs: list[SocketSerialize]
    content: ContentSerialize


class Node(Serializable):
    def __init__(self, scene: "Scene", title: str = "Undefined Node",
                 inputs: list[int] | None = None,
                 outputs: list[int] | None = None) -> None:
        super().__init__()
        self._title = title  # FIXME: title is used from within QDMGraphicsNode constructor
        self.scene = scene
        self.init_gui_objects()
        self.init_settings()
        self.title = title

        self.scene.add_node(self)
        self.scene.gr_scene.addItem(self.gr_node)

        self.inputs: list[Socket] = []
        self.outputs: list[Socket] = []
        self.init_sockets(inputs, outputs)

    def init_gui_objects(self) -> None:
        self.content = QDMContentWidget(self)
        self.gr_node = QDMGraphicsNode(self)

    def init_settings(self) -> None:
        self.socket_spacing = 22
        self.input_socket_position = Pos.LEFT_BOTTOM
        self.output_socket_position = Pos.RIGHT_TOP
        self.input_multi_edged = False
        self.output_multi_edged = True

    def init_sockets(self, inputs: list[int] | None, outputs: list[int] | None,
                     *, reset: bool = True) -> None:
        "Create sockets for inputs and outputs."
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

    def __str__(self):
        return f"<Node ..{hex(id(self))[-5:]} '{self.title}'>"

    @property
    def pos(self):
        "Node position in a scene"
        return self.gr_node.pos()

    def set_pos(self, x: float, y: float):
        self.gr_node.setPos(x, y)

    @property
    def title(self):
        "Set text in node header area."
        return self._title

    @title.setter
    def title(self, value: str):
        self._title = value
        self.gr_node.title = value

    def get_socket_position(self, index: int, position: Pos,
                            socket_count_on_side: int = 1) -> tuple[float, float]:
        "Get socket element x,y position by its index."
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

    def update_connected_edges(self):
        "Update location of edges connected to the node."
        for socket in self.inputs + self.outputs:
            for edge in socket.edges:
                edge.update_positions()

    def remove(self):
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

    def deserialize(self, data: NodeSerialize, hashmap: dict, restore_id=True):
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
            new_socket.deserialize(socket_data, hashmap, restore_id)
            self.inputs.append(new_socket)

        self.outputs = []
        for socket_data in data["outputs"]:
            new_socket = Socket(node=self, index=socket_data["index"],
                                position=socket_data["position"],
                                socket_type=socket_data["socket_type"],
                                socket_count_on_side=len(data["outputs"]),
                                is_input=False)
            new_socket.deserialize(socket_data, hashmap, restore_id)
            self.outputs.append(new_socket)

        return True
