"""
Node
"""
import logging

from qt_node_editor.node_content_widget import QDMContentWidget
from qt_node_editor.node_graphics_node import QDMGraphicsNode
from qt_node_editor.node_scene import Scene
from qt_node_editor.node_serializable import Serializable
from qt_node_editor.node_socket import Pos, Socket

log = logging.getLogger(__name__)


class Node(Serializable):
    def __init__(self, scene: Scene, title="Undefined Node",
                 inputs: list[int] | None = None,
                 outputs: list[int] | None = None) -> None:
        super().__init__()
        self.scene = scene
        self.title = title

        self.content = QDMContentWidget(self)
        self.gr_node = QDMGraphicsNode(self)
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
    
    def serialize(self):
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

    def deserialize(self, data, hashmap: dict = {}):
        return False
