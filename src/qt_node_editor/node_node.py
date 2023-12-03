"""
Node
"""
import logging
from typing import TYPE_CHECKING, TypedDict

from qt_node_editor.node_content_widget import QDMContentWidget
from qt_node_editor.node_graphics_node import QDMGraphicsNode
from qt_node_editor.node_serializable import Serializable
from qt_node_editor.node_socket import Pos, Socket

if TYPE_CHECKING:
    from qt_node_editor.node_scene import Scene

log = logging.getLogger(__name__)
NodeSerialize = TypedDict('NodeSerialize', {
    'id': int, 'title': str, 'pos_x': float, 'pos_y': float,
    'inputs': list[dict], 'outputs': list[dict], 'content': dict
})


class Node(Serializable):
    def __init__(self, scene: "Scene", title="Undefined Node",
                 inputs: list[int] | None = None,
                 outputs: list[int] | None = None) -> None:
        super().__init__()
        self._title = title  # FIXME: title is used from within QDMGraphicsNode constructor
        self.scene = scene
        self.content = QDMContentWidget(self)
        self.gr_node = QDMGraphicsNode(self)
        self.title = title

        self.scene.add_node(self)
        self.scene.gr_scene.addItem(self.gr_node)

        self.socket_spacing = 22

        self.inputs: list[Socket] = []
        self.outputs: list[Socket] = []
        for counter, item in enumerate(inputs or []):
            socket = Socket(self, index=counter, position=Pos.LEFT_BOTTOM,
                            socket_type=item)
            self.inputs.append(socket)
        for counter, item in enumerate(outputs or []):
            socket = Socket(self, index=counter, position=Pos.RIGHT_TOP,
                            socket_type=item)
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

    def get_socket_position(self, index: int, position: Pos):
        "Get socket element x,y position by its index."
        x = 0 if position in (Pos.LEFT_TOP, Pos.LEFT_BOTTOM) else \
            self.gr_node.width
        if position in (Pos.LEFT_BOTTOM, Pos.RIGHT_BOTTOM):
            # FIXME: _padding is protected and is used for node title only
            y = self.gr_node.height - self.gr_node._padding - \
                self.gr_node.edge_size - index * self.socket_spacing
        else:
            y = self.gr_node.title_height + self.gr_node._padding + \
                self.gr_node.edge_size + index * self.socket_spacing
        return [x, y]

    def update_connected_edges(self):
        "Update location of edges connected to the node."
        for socket in self.inputs + self.outputs:
            if socket.has_edge():
                socket.edge.update_positions()

    def remove(self):
        log.debug("> Removing node %s", self)
        log.debug(" - remove all edges from sockets")
        for socket in (self.inputs + self.outputs):
            if socket.has_edge():
                log.debug("    - removing from socket %s edge %s", socket,  socket.edge)
                socket.edge.remove()
        log.debug(" - remove gr_node")
        self.scene.gr_scene.removeItem(self.gr_node)
        self.gr_node = None
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
                                socket_type=socket_data["socket_type"])
            new_socket.deserialize(socket_data, hashmap, restore_id)
            self.inputs.append(new_socket)

        self.outputs = []
        for socket_data in data["outputs"]:
            new_socket = Socket(node=self, index=socket_data["index"],
                                position=socket_data["position"],
                                socket_type=socket_data["socket_type"])
            new_socket.deserialize(socket_data, hashmap, restore_id)
            self.outputs.append(new_socket)

        return True
