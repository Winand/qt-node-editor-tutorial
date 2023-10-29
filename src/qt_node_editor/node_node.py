from qt_node_editor.node_graphics_node import QDMGraphicsNode
from qt_node_editor.node_scene import Scene


class Node():
    def __init__(self, scene: Scene, title="Undefined Node") -> None:
        self.scene = scene
        self.title = title

        self.gr_node = QDMGraphicsNode(self, self.title)
        self.scene.add_node(self)
        self.scene.gr_scene.addItem(self.gr_node)

        self.gr_node.title = 'abracadabra'

        self.inputs = []
        self.outputs = []
