from qtpy.QtCore import Qt
from qtpy.QtWidgets import QWidget

from qt_node_editor.node_editor_widget import NodeEditorWidget


class CalculatorSubWindow(NodeEditorWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.set_title()

        self.scene.add_has_been_modified_listener(self.set_title)

    def set_title(self):
        self.setWindowTitle(self.get_user_friendly_filename())
