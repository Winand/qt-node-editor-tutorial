from pathlib import Path
from typing import cast

from qtpy.QtWidgets import (QAction, QFileDialog, QLabel, QMainWindow, QMenu,
                            QMenuBar, QStatusBar)

from qt_node_editor.node_editor_widget import NodeEditorWidget


class NodeEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.filename = None

    def create_act(self, name: str, shortcut: str, tooltip: str, callback):
        act = QAction(name, self)
        act.setShortcut(shortcut)
        act.setToolTip(tooltip)
        act.triggered.connect(callback)
        return act

    def init_ui(self):
        menu_bar = cast(QMenuBar, self.menuBar())

        file_menu = cast(QMenu, menu_bar.addMenu('&File'))
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

        edit_menu = cast(QMenu, menu_bar.addMenu("&Edit"))
        edit_menu.addAction(self.create_act(
            '&Undo', 'Ctrl+Z', "Undo last operation", self.on_edit_undo
        ))
        edit_menu.addAction(self.create_act(
            '&Redo', 'Ctrl+Y', "Redo last operation", self.on_edit_redo
        ))
        edit_menu.addSeparator()
        edit_menu.addAction(self.create_act(
            '&Delete', 'Del', "Delete selected items", self.on_edit_delete
        ))

        nodeeditor = NodeEditorWidget(self)
        self.setCentralWidget(nodeeditor)

        self.status_mouse_pos = QLabel("")
        cast(QStatusBar, self.statusBar()).addPermanentWidget(self.status_mouse_pos)
        nodeeditor.view.scene_pos_changed.connect(self.on_scene_pos_changed)

        # Set window properties
        self.setGeometry(200, 200, 800, 600)
        self.setWindowTitle("Node Editor")
        self.show()

    def on_scene_pos_changed(self, x: int, y: int):
        self.status_mouse_pos.setText(f"Scene Pos: {x}, {y}")

    def on_file_new(self):
        cast(NodeEditorWidget, self.centralWidget()).scene.clear()

    def on_file_open(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open graph from file')
        if fname == '':
            return
        if Path(fname).is_file():
            cast(NodeEditorWidget, self.centralWidget()) \
                .scene.load_from_file(fname)

    def on_file_save(self):
        if self.filename is None:
            return self.on_file_save_as()
        cast(NodeEditorWidget, self.centralWidget()) \
            .scene.save_to_file(self.filename)
        cast(QStatusBar, self.statusBar()) \
            .showMessage(f"Successfully saved {self.filename}")

    def on_file_save_as(self):
        fname, _ = QFileDialog.getSaveFileName(self, 'Save graph to file')
        if fname == '':
            return
        self.filename = fname
        self.on_file_save()

    def on_edit_undo(self):
        cast(NodeEditorWidget, self.centralWidget()).scene.history.undo()

    def on_edit_redo(self):
        cast(NodeEditorWidget, self.centralWidget()).scene.history.redo()

    def on_edit_delete(self):
        cast(NodeEditorWidget, self.centralWidget()) \
            .scene.gr_scene.views()[0].delete_selected()  # FIXME:
