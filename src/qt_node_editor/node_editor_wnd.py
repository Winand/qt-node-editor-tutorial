import pkgutil
from typing import cast

from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QColor, QFont, QPen
from qtpy.QtWidgets import (QApplication, QGraphicsItem, QGraphicsLineItem,
                            QGraphicsProxyWidget, QGraphicsRectItem,
                            QGraphicsTextItem, QPushButton, QTextEdit,
                            QVBoxLayout, QWidget)

from qt_node_editor.node_edge import Edge, EdgeType
from qt_node_editor.node_graphics_view import QDMGraphicsView
from qt_node_editor.node_node import Node
from qt_node_editor.node_scene import Scene

GraphicsItemFlag = QGraphicsItem.GraphicsItemFlag


class NodeEditorWnd(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.stylesheet_filename = "qss/nodestyle.qss"
        self.loadStylesheet(self.stylesheet_filename)
        self.init_ui()

    def init_ui(self):
        self.setGeometry(200, 200, 800, 600)
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        # create graphics scene
        self.scene = Scene()
        # self.gr_scene = self.scene.gr_scene

        self.add_nodes()

        # create graphics view
        self.view = QDMGraphicsView(self.scene, self)
        self._layout.addWidget(self.view)

        self.setWindowTitle("Node Editor")
        self.show()

        # self.add_debug_content()

    def add_nodes(self):
        node1 = Node(self.scene, "My Awesome Node 1",
                    inputs=[0, 0, 0], outputs=[1])
        node2 = Node(self.scene, "My Awesome Node 2",
                    inputs=[3, 3, 3], outputs=[1])
        node3 = Node(self.scene, "My Awesome Node 3",
                    inputs=[2, 2, 2], outputs=[1])
        node1.set_pos(-350, -250)
        node2.set_pos(-75, 0)
        node3.set_pos(200, -150)

        edge1 = Edge(self.scene, node1.outputs[0], node2.inputs[0],
                     shape=EdgeType.Bezier)
        edge2 = Edge(self.scene, node2.outputs[0], node3.inputs[0],
                     shape=EdgeType.Bezier)

    def add_debug_content(self):
        green_brush = QBrush(Qt.GlobalColor.green)  # see also QtGui.QColorConstants
        outline_pen = QPen(Qt.GlobalColor.black)
        outline_pen.setWidth(2)
        rect = cast(QGraphicsRectItem,
                    self.scene.gr_scene.addRect(-100, -100, 80, 100, outline_pen, green_brush))
        rect.setFlag(GraphicsItemFlag.ItemIsMovable)

        text = cast(QGraphicsTextItem,
                    self.scene.gr_scene.addText("This is my awesome text",
                                          QFont("Verdana")))
        text.setFlag(GraphicsItemFlag.ItemIsSelectable)
        text.setFlag(GraphicsItemFlag.ItemIsMovable)
        text.setDefaultTextColor(QColor.fromRgbF(1., 1., 1.))

        widget1 = QPushButton("Hello World!")
        proxy1 = cast(QGraphicsProxyWidget, self.scene.gr_scene.addWidget(widget1))
        proxy1.setFlag(GraphicsItemFlag.ItemIsMovable)
        proxy1.setPos(0, 30)

        widget2 = QTextEdit()
        proxy2 = cast(QGraphicsProxyWidget,
                      self.scene.gr_scene.addWidget(widget2))
        proxy2.setFlag(GraphicsItemFlag.ItemIsSelectable)
        proxy2.setPos(0, 60)

        line = cast(QGraphicsLineItem,
                    self.scene.gr_scene.addLine(-200, -200, 400, -100, outline_pen))
        line.setFlag(GraphicsItemFlag.ItemIsMovable | GraphicsItemFlag.ItemIsSelectable)

    def loadStylesheet(self, filename: str):
        print(f"Style loading: {filename}")
        # Load file from package https://stackoverflow.com/a/58941536
        if (stylesheet := pkgutil.get_data(__name__, filename)) is None:
            raise FileNotFoundError(f"Cannot load {filename}")
        cast(QApplication, QApplication.instance()) \
            .setStyleSheet(stylesheet.decode())
