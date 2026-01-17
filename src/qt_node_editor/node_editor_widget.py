"""
Module with `NodeEditorWidget` class containing view with a scene.

`NodeEditorWidget` also has interface for creating, loading and saving documents.
"""
import logging
from pathlib import Path

from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QColor, QFont, QPen
from qtpy.QtWidgets import (
    QApplication,
    QGraphicsItem,
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
from qt_node_editor.utils import format_exception_chain, some

GraphicsItemFlag = QGraphicsItem.GraphicsItemFlag
log = logging.getLogger(__name__)


class NodeEditorWidget(QWidget):
    "Container for a graphics view with a scene."

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize :class:`NodeEditorWidget`.

        :param parent: parent widget or ``None``
        """
        super().__init__(parent)

        self.filename: Path | None = None  #: current document file path or ``None``

        self._init_ui()

    def _init_ui(self) -> None:
        "Set up :doc:`view <qt_node_editor.node_graphics_view>` and :class:`.Scene`."
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
        """
        Get document name from the file path if the document was saved.

        Return default name for unsaved documents.
        Adds "*" if the document has unsaved changes.
        """
        name = self.filename.name if self.filename is not None else "New Graph"
        return name + ("*" if self.is_modified else "")

    def new_file(self) -> None:
        "Reset the scene and current file name."
        self.scene.clear()
        self.filename = None
        self.scene.history.clear()
        self.scene.history.store_initial_history_stamp()

    def load_file(self, filename: Path) -> bool:
        """
        Load a scene from a file.

        :param filename: file path to load from
        :return: ``True`` if a file was loaded successfully
        """
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
        """
        Save the scene to a file.

        Remembers `filename` as current document file path. If called without
        `filename` parameter specified that file path is required to be set before.

        :param filename: file path to save to
        :return: ``True`` if a file was saved successfully
        """
        if filename:
            self.filename = filename  # TODO: unnecessary side effect?
        assert self.filename, "File name is required to save the scene."
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.scene.save_to_file(self.filename)
        QApplication.restoreOverrideCursor()
        return True

    def add_nodes(self) -> None:
        "Add 3 example nodes and 2 edges to the scene."
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

    def add_debug_content(self) -> None:
        "Put several test graphics elements on the scene."
        green_brush = QBrush(Qt.GlobalColor.green)  # see also QtGui.QColorConstants
        outline_pen = QPen(Qt.GlobalColor.black)
        outline_pen.setWidth(2)
        rect = some(self.scene.gr_scene.addRect(-100, -100, 80, 100,
                                                outline_pen, green_brush))
        rect.setFlag(GraphicsItemFlag.ItemIsMovable)

        text = some(self.scene.gr_scene.addText("This is my awesome text",
                                                QFont("Verdana")))
        text.setFlag(GraphicsItemFlag.ItemIsSelectable)
        text.setFlag(GraphicsItemFlag.ItemIsMovable)
        text.setDefaultTextColor(QColor.fromRgbF(1., 1., 1.))

        widget1 = QPushButton("Hello World!")
        proxy1 = some(self.scene.gr_scene.addWidget(widget1))
        proxy1.setFlag(GraphicsItemFlag.ItemIsMovable)
        proxy1.setPos(0, 30)

        widget2 = QTextEdit()
        proxy2 = some(self.scene.gr_scene.addWidget(widget2))
        proxy2.setFlag(GraphicsItemFlag.ItemIsSelectable)
        proxy2.setPos(0, 60)

        line = some(self.scene.gr_scene.addLine(-200, -200, 400, -100, outline_pen))
        line.setFlag(GraphicsItemFlag.ItemIsMovable | GraphicsItemFlag.ItemIsSelectable)

    def __del__(self) -> None:
        "Node editor widget destruction event."
        log.debug("delete editor widget")
        # import gc
        # from PyQt6.QtCore import QTimer
        # QTimer.singleShot(0, gc.collect)
