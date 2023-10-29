from qt_node_editor.node_graphics_node import QDMGraphicsNode
from qt_node_editor.node_scene import Scene
from qt_node_editor.node_content_widget import QDMContentWidget


class Node():
    def __init__(self, scene: Scene, title="Undefined Node") -> None:
        self.scene = scene
        self.title = title

        self.content = QDMContentWidget()
        self.gr_node = QDMGraphicsNode(self)
        self.scene.add_node(self)
        self.scene.gr_scene.addItem(self.gr_node)

        self.inputs = []
        self.outputs = []
