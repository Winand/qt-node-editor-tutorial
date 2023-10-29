from typing import cast

from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QColor, QFont, QPen
from qtpy.QtWidgets import (QGraphicsItem, QGraphicsLineItem,
                            QGraphicsProxyWidget, QGraphicsRectItem,
                            QGraphicsTextItem, QPushButton, QTextEdit,
                            QVBoxLayout, QWidget)

from qt_node_editor.node_scene import Scene
from qt_node_editor.node_graphics_view import QDMGraphicsView

GraphicsItemFlag = QGraphicsItem.GraphicsItemFlag


class NodeEditorWnd(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setGeometry(200, 200, 800, 600)
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        # create graphics scene
        self.scene = Scene()
        self.gr_scene = self.scene.gr_scene

        # create graphics view
        self.view = QDMGraphicsView(self.gr_scene, self)
        self._layout.addWidget(self.view)

        self.setWindowTitle("Node Editor")
        self.show()


        self.add_debug_content()


    def add_debug_content(self):
        green_brush = QBrush(Qt.GlobalColor.green)  # see also QtGui.QColorConstants
        outline_pen = QPen(Qt.GlobalColor.black)
        outline_pen.setWidth(2)
        rect = cast(QGraphicsRectItem,
                    self.gr_scene.addRect(-100, -100, 80, 100, outline_pen, green_brush))
        rect.setFlag(GraphicsItemFlag.ItemIsMovable)

        text = cast(QGraphicsTextItem,
                    self.gr_scene.addText("This is my awesome text",
                                          QFont("Verdana")))
        text.setFlag(GraphicsItemFlag.ItemIsSelectable)
        text.setFlag(GraphicsItemFlag.ItemIsMovable)
        text.setDefaultTextColor(QColor.fromRgbF(1., 1., 1.))

        widget1 = QPushButton("Hello World!")
        proxy1 = cast(QGraphicsProxyWidget, self.gr_scene.addWidget(widget1))
        proxy1.setFlag(GraphicsItemFlag.ItemIsMovable)
        proxy1.setPos(0, 30)

        widget2 = QTextEdit()
        proxy2 = cast(QGraphicsProxyWidget,
                      self.gr_scene.addWidget(widget2))
        proxy2.setFlag(GraphicsItemFlag.ItemIsSelectable)
        proxy2.setPos(0, 60)

        line = cast(QGraphicsLineItem,
                    self.gr_scene.addLine(-200, -200, 400, -100, outline_pen))
        line.setFlag(GraphicsItemFlag.ItemIsMovable | GraphicsItemFlag.ItemIsSelectable)
