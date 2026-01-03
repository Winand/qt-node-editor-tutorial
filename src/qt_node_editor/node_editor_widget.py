import logging
from pathlib import Path
from typing import cast

from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QColor, QFont, QPen
from qtpy.QtWidgets import (
    QApplication,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsProxyWidget,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from qt_node_editor.node_edge import Edge, EdgeType
from qt_node_editor.node_graphics_view import QDMGraphicsView
from qt_node_editor.node_node import Node
from qt_node_editor.node_scene import InvalidSceneFileError, Scene
from qt_node_editor.utils import format_exception_chain

GraphicsItemFlag = QGraphicsItem.GraphicsItemFlag
log = logging.getLogger(__name__)


class NodeEditorWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.filename: Path | None = None

        self.init_ui()

    def init_ui(self):
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        # create graphics scene
        self.scene = Scene()

        # create graphics view
        self.view = QDMGraphicsView(self.scene, self)
        self._layout.addWidget(self.view)

        # self.add_debug_content()

    @property
    def is_modified(self) -> bool:
        "Return True if the scene has been modified."
        return self.scene.has_been_modified

    def get_selected_items(self) -> list[QGraphicsItem]:
        "Get a list of selected elements on the editor scene."
        return self.scene.get_selected_items()

    def has_selected_items(self) -> bool:
        "Check if there are selected elements on the scene."
        return len(self.get_selected_items()) > 0

    def can_undo(self) -> bool:
        "Check if undo action is available on the scene."
        return self.scene.history.can_undo()

    def can_redo(self) -> bool:
        "Check if redo action is available on the scene."
        return self.scene.history.can_redo()

    def get_user_friendly_filename(self) -> str:
        name = self.filename.name if self.filename is not None else "New Graph"
        return name + ("*" if self.is_modified else "")

    def new_file(self) -> None:
        "Reset the scene and current file name."
        self.scene.clear()
        self.filename = None
        self.scene.history.clear()
        self.scene.history.store_initial_history_stamp()

    def load_file(self, filename: Path) -> bool:
        "Load a scene from a file."
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.scene.load_from_file(filename)
        except InvalidSceneFileError as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(
                self, f"Error loading {filename.name}", format_exception_chain(e),
            )
            return False
        self.filename = filename
        self.scene.history.clear()
        self.scene.history.store_initial_history_stamp()
        QApplication.restoreOverrideCursor()
        return True

    def save_file(self, filename: Path | None = None) -> bool:
        "Save the scene to a file."
        if filename:
            self.filename = filename  # TODO: unnecessary side effect?
        assert self.filename, "File name is required to save the scene."
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.scene.save_to_file(self.filename)
        QApplication.restoreOverrideCursor()
        return True

    def add_nodes(self) -> None:
        "Add some example nodes to the scene."
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
                     shape=EdgeType.BEZIER)
        edge2 = Edge(self.scene, node2.outputs[0], node3.inputs[0],
                     shape=EdgeType.BEZIER)

        self.scene.history.store_initial_history_stamp()

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

    def __del__(self) -> None:
        log.debug("delete editor widget")
        # import gc
        # from PyQt6.QtCore import QTimer
        # QTimer.singleShot(0, gc.collect)
