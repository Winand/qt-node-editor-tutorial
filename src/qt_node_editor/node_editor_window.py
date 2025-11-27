import json
import logging
from collections.abc import Callable
from pathlib import Path

import typedload
from qtpy.QtGui import QAction, QGuiApplication
from qtpy.QtWidgets import QApplication, QFileDialog, QLabel, QMainWindow

from qt_node_editor.node_editor_widget import NodeEditorWidget
from qt_node_editor.node_graphics_view import QDMGraphicsView
from qt_node_editor.node_scene import SceneSerialize
from qt_node_editor.utils import As, some

log = logging.getLogger(__name__)


class NodeEditorWindow(QMainWindow):
    centralWidget: Callable[[], NodeEditorWidget]  # noqa: N815

    def __init__(self):
        super().__init__()
        self.app = QApplication.instance() @As(QGuiApplication)
        self.init_ui()
        self.filename = None

    def create_act(self, name: str, shortcut: str, tooltip: str, callback):
        act = QAction(name, self)
        act.setShortcut(shortcut)
        act.setToolTip(tooltip)
        act.triggered.connect(callback)
        return act

    def init_ui(self):
        menu_bar = some(self.menuBar())

        file_menu = some(menu_bar.addMenu('&File'))
        file_menu.addAction(self.create_act(
            '&New', 'Ctrl+N', "Create new graph", self.on_file_new
        ))
        file_menu.addSeparator()
        file_menu.addAction(self.create_act(
            '&Open', 'Ctrl+O', "Open file", self.on_file_open
        ))
        file_menu.addAction(self.create_act(
            '&Save', 'Ctrl+S', "Save file", self.on_file_save
        ))
        file_menu.addAction(self.create_act(
            'Save &As...', 'Ctrl+Shift+S', "Save file as...", self.on_file_save_as
        ))
        file_menu.addSeparator()
        file_menu.addAction(self.create_act(
            'E&xit', 'Ctrl+Q', "Exit application", self.close
        ))

        edit_menu = some(menu_bar.addMenu("&Edit"))
        edit_menu.addAction(self.create_act(
            '&Undo', 'Ctrl+Z', "Undo last operation", self.on_edit_undo
        ))
        edit_menu.addAction(self.create_act(
            '&Redo', 'Ctrl+Y', "Redo last operation", self.on_edit_redo
        ))
        edit_menu.addSeparator()
        edit_menu.addAction(self.create_act(
            'Cu&t', 'Ctrl+X', "Cut to clipboard", self.on_edit_cut
        ))
        edit_menu.addAction(self.create_act(
            '&Copy', 'Ctrl+C', "Copy to clipboard", self.on_edit_copy
        ))
        edit_menu.addAction(self.create_act(
            '&Paste', 'Ctrl+V', "Paste from clipboard", self.on_edit_paste
        ))
        edit_menu.addSeparator()
        edit_menu.addAction(self.create_act(
            '&Delete', 'Del', "Delete selected items", self.on_edit_delete
        ))

        nodeeditor = NodeEditorWidget(self)
        self.setCentralWidget(nodeeditor)

        self.status_mouse_pos = QLabel("")
        some(self.statusBar()).addPermanentWidget(self.status_mouse_pos)
        nodeeditor.view.scene_pos_changed.connect(self.on_scene_pos_changed)

        # Set window properties
        self.setGeometry(200, 200, 800, 600)
        self.setWindowTitle("Node Editor")
        self.show()


    def on_scene_pos_changed(self, x: int, y: int):
        self.status_mouse_pos.setText(f"Scene Pos: {x}, {y}")

    def on_file_new(self):
        self.centralWidget().scene.clear()

    def on_file_open(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open graph from file',
                                               filter="JSON files (*.json)")
        if fname == '':
            return
        if Path(fname).is_file():
            self.centralWidget().scene.load_from_file(fname)

    def on_file_save(self):
        if self.filename is None:
            return self.on_file_save_as()
        self.centralWidget().scene.save_to_file(self.filename)
        some(self.statusBar()).showMessage(f"Successfully saved {self.filename}")

    def on_file_save_as(self):
        fname, _ = QFileDialog.getSaveFileName(self, 'Save graph to file',
                                               filter="JSON files (*.json)")
        if fname == '':
            return
        self.filename = fname
        self.on_file_save()

    def on_edit_undo(self):
        self.centralWidget().scene.history.undo()

    def on_edit_redo(self):
        self.centralWidget().scene.history.redo()

    def on_edit_delete(self):
        view = self.centralWidget().scene.gr_scene.views()[0] @As(QDMGraphicsView)
        view.delete_selected()

    def on_edit_cut(self):
        data = self.centralWidget().scene.clipboard.serialize_selected(delete=True)
        str_data = json.dumps(data, indent=4)
        some(self.app.clipboard()).setText(str_data)

    def on_edit_copy(self):
        data = self.centralWidget().scene.clipboard.serialize_selected(delete=False)
        str_data = json.dumps(data, indent=4)
        some(self.app.clipboard()).setText(str_data)

    def on_edit_paste(self):
        raw_data = some(self.app.clipboard()).text()

        try:
            json_data = json.loads(raw_data)
        except ValueError as e:
            log.error("Pasting of not valid json data! %s", e)
            return

        try:
            data = typedload.load(json_data, SceneSerialize)
        except (ValueError, TypeError) as e:
            log.error("JSON is not a valid scene: %s", e)
            return
        self.centralWidget().scene.clipboard.deserialize_from_clipboard(data)
