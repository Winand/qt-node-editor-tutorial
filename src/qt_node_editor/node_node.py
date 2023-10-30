from qt_node_editor.node_graphics_node import QDMGraphicsNode
from qt_node_editor.node_scene import Scene
from qt_node_editor.node_socket import Socket, POS
from qt_node_editor.node_content_widget import QDMContentWidget


class Node():
    def __init__(self, scene: Scene, title="Undefined Node",
                 inputs: list[Socket] | None = None,
                 outputs: list[Socket] | None = None) -> None:
        self.scene = scene
        self.title = title

        self.content = QDMContentWidget()
        self.gr_node = QDMGraphicsNode(self)
        self.scene.add_node(self)
        self.scene.gr_scene.addItem(self.gr_node)

        self.socket_spacing = 22

        self.inputs = []
        self.outputs = []
        for counter, item in enumerate(inputs or []):
            socket = Socket(self, index=counter, position=POS.LEFT_BOTTOM)
            self.inputs.append(socket)
        for counter, item in enumerate(outputs or []):
            socket = Socket(self, index=counter, position=POS.RIGHT_TOP)
            self.outputs.append(socket)

    @property
    def pos(self):
        "Node position in a scene"
        return self.gr_node.pos()

    def set_pos(self, x: float, y: float):
        self.gr_node.setPos(x, y)

    def get_socket_position(self, index: int, position: POS):
        "Get socket element x,y position by its index."
        x = 0 if position in (POS.LEFT_TOP, POS.LEFT_BOTTOM) else \
            self.gr_node.width
        if position in (POS.LEFT_BOTTOM, POS.RIGHT_BOTTOM):
            # FIXME: _padding is protected and is used for node title only
            y = self.gr_node.height - self.gr_node._padding - \
                self.gr_node.edge_size - index * self.socket_spacing
        else:
            y = self.gr_node.title_height + self.gr_node._padding + \
                self.gr_node.edge_size + index * self.socket_spacing
        return x, y
