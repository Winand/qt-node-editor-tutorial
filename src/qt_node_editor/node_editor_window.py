from typing import cast

from qtpy.QtWidgets import QAction, QMainWindow, QMenu, QMenuBar

from qt_node_editor.node_editor_widget import NodeEditorWidget


class NodeEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

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

        nodeeditor = NodeEditorWidget(self)
        self.setCentralWidget(nodeeditor)

        # Set window properties
        self.setGeometry(200, 200, 800, 600)
        self.setWindowTitle("Node Editor")
        self.show()

    def on_file_new(self):
        print("On File New clicked")

    def on_file_open(self):
        print("On FileOpen clicked")

    def on_file_save(self):
        print("On FileSave clicked")

    def on_file_save_as(self):
        print("On FileSaveAs clicked")
