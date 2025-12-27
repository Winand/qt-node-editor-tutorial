from collections.abc import Callable
from typing import override

from PyQt6.QtGui import QCloseEvent
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QWidget

from qt_node_editor.node_editor_widget import NodeEditorWidget

CloseEventCallback = Callable[["CalculatorSubWindow", QCloseEvent | None], None]


class CalculatorSubWindow(NodeEditorWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.set_title()

        self.scene.add_has_been_modified_listener(self.set_title)

        self._close_event_listeners: list[CloseEventCallback] = []

    def set_title(self):
        self.setWindowTitle(self.get_user_friendly_filename())

    def add_close_event_listener(self, callback: CloseEventCallback) -> None:
        """
        Add a new callback to be called when the scene is modified.

        :param callback: A callback function
        :type callback: Callable[[], None]
        """
        self._close_event_listeners.append(callback)

    @override
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        for callback in self._close_event_listeners:
            callback(self, a0)
        # cleanup! https://www.youtube.com/watch?v=C29ftCo9h50&lc=Ugw-gQlXQ8CMU2OXnDV4AaABAg
        self.scene.rem_has_been_modified_listener(self.set_title)
