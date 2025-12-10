import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import override

import typedload
from qtpy.QtCore import QPoint, QSettings, QSize
from qtpy.QtGui import QAction, QCloseEvent, QGuiApplication, QKeySequence
from qtpy.QtWidgets import QApplication, QFileDialog, QLabel, QMainWindow, QMessageBox
from typedload.exceptions import TypedloadException

from qt_node_editor.node_editor_widget import NodeEditorWidget
from qt_node_editor.node_graphics_view import QDMGraphicsView
from qt_node_editor.node_scene import SceneSerialize
from qt_node_editor.utils import As, some

log = logging.getLogger(__name__)


class NodeEditorWindow(QMainWindow):
    centralWidget: Callable[[], NodeEditorWidget]  # pyright: ignore[reportIncompatibleMethodOverride] # noqa: N815

    def __init__(self):
        super().__init__()
        self.app = QApplication.instance() @As(QGuiApplication)
        self.filename: str | None = None
        self.init_ui()

    def create_act(self, name: str, callback: Callable[[], bool | None],
                   shortcut: str | QKeySequence.StandardKey = "", tooltip: str = "") -> QAction:
        act = QAction(name, self)
        if shortcut:
            act.setShortcut(shortcut)
        if tooltip:
            act.setToolTip(tooltip)
        act.triggered.connect(callback)
        return act

    def init_ui(self):
        self.name_company = "Winand"
        self.name_product = "NodeEditor"

        self.create_menus()

        nodeeditor = NodeEditorWidget(self)
        nodeeditor.scene.add_has_been_modified_listener(self.change_title)
        self.setCentralWidget(nodeeditor)

        self.create_status_bar()

        # Set window properties
        self.setGeometry(200, 200, 800, 600)
        self.change_title()
        self.show()

    def create_status_bar(self) -> None:
        some(self.statusBar()).showMessage("")
        self.status_mouse_pos = QLabel("")
        some(self.statusBar()).addPermanentWidget(self.status_mouse_pos)
        self.centralWidget().view.scene_pos_changed.connect(self.on_scene_pos_changed)

    def create_menus(self) -> None:
        menu_bar = some(self.menuBar())

        file_menu = some(menu_bar.addMenu('&File'))
        file_menu.addAction(self.create_act(
            '&New', self.on_file_new, 'Ctrl+N', "Create new graph",
        ))
        file_menu.addSeparator()
        file_menu.addAction(self.create_act(
            '&Open', self.on_file_open, 'Ctrl+O', "Open file",
        ))
        file_menu.addAction(self.create_act(
            '&Save', self.on_file_save, 'Ctrl+S', "Save file",
        ))
        file_menu.addAction(self.create_act(
            'Save &As...', self.on_file_save_as, 'Ctrl+Shift+S', "Save file as...",
        ))
        file_menu.addSeparator()
        file_menu.addAction(self.create_act(
            'E&xit', self.close, 'Ctrl+Q', "Exit application",
        ))

        edit_menu = some(menu_bar.addMenu("&Edit"))
        edit_menu.addAction(self.create_act(
            '&Undo', self.on_edit_undo, 'Ctrl+Z', "Undo last operation",
        ))
        edit_menu.addAction(self.create_act(
            '&Redo', self.on_edit_redo, 'Ctrl+Y', "Redo last operation",
        ))
        edit_menu.addSeparator()
        edit_menu.addAction(self.create_act(
            'Cu&t', self.on_edit_cut, 'Ctrl+X', "Cut to clipboard",
        ))
        edit_menu.addAction(self.create_act(
            '&Copy', self.on_edit_copy, 'Ctrl+C', "Copy to clipboard",
        ))
        edit_menu.addAction(self.create_act(
            '&Paste', self.on_edit_paste, 'Ctrl+V', "Paste from clipboard",
        ))
        edit_menu.addSeparator()
        edit_menu.addAction(self.create_act(
            '&Delete', self.on_edit_delete, 'Del', "Delete selected items",
        ))

    def change_title(self) -> None:
        "Update window title."
        title = "Node Editor - "
        if not self.filename:
            title += "New"
        else:
            title += Path(self.filename).name

        if self.centralWidget().scene.has_been_modified:
            title += "*"
        self.setWindowTitle(title)

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        "Ignore window close event if user cancels the save dialog."
        if self.maybe_save():
            event.accept()
        else:
            event.ignore()

    @property
    def modified(self) -> bool:
        "Checks if the document has been modified."
        try:
            return self.centralWidget().scene.has_been_modified
        except AttributeError as e:
            print(e)
            return False

    def maybe_save(self) -> bool:
        "Check if the document has unsaved changes and save if requested."
        if not self.modified:
            return True
        sb = QMessageBox.StandardButton
        res = QMessageBox.warning(
            self, "About to lose your work?",
            "The document has been modified.\nDo you want to save changes?",
            sb.Save | sb.Discard | sb.Cancel,
        )
        if res == sb.Save:
            return self.on_file_save()
        return res == sb.Discard

    def on_scene_pos_changed(self, x: int, y: int):
        self.status_mouse_pos.setText(f"Scene Pos: {x}, {y}")

    def on_file_new(self):
        if self.maybe_save():
            self.centralWidget().scene.clear()
            self.filename = None
            self.change_title()

    def on_file_open(self):
        if self.maybe_save():
            fname, _ = QFileDialog.getOpenFileName(self, 'Open graph from file',
                                                   filter="JSON files (*.json)")
            if fname == '':
                return
            if Path(fname).is_file():
                try:
                    self.centralWidget().scene.load_from_file(fname)
                except TypedloadException as e:
                    QMessageBox.critical(self, "File load error", str(e))
                    return
                self.filename = fname
                self.change_title()

    def on_file_save(self) -> bool:
        if self.filename is None:
            return self.on_file_save_as()
        self.centralWidget().scene.save_to_file(self.filename)
        some(self.statusBar()).showMessage(f"Successfully saved {self.filename}")
        return True

    def on_file_save_as(self) -> bool:
        fname, _ = QFileDialog.getSaveFileName(self, 'Save graph to file',
                                               filter="JSON files (*.json)")
        if fname == '':
            return False
        self.filename = fname
        return self.on_file_save()

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

    def read_settings(self):
        settings = QSettings(self.name_company, self.name_product)
        pos = settings.value("pos", QPoint(200, 200))
        size = settings.value("size", QSize(400, 400))
        self.move(pos)
        self.resize(size)

    def write_settings(self):
        settings = QSettings(self.name_company, self.name_product)
        settings.setValue("pos", self.pos())
        settings.setValue("size", self.size())
