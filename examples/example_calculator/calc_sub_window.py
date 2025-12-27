from collections.abc import Callable
from typing import TYPE_CHECKING, override

from PyQt6.QtGui import QCloseEvent
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QWidget

from qt_node_editor.node_editor_widget import NodeEditorWidget
from qt_node_editor.utils import ref

if TYPE_CHECKING:
    from weakref import ReferenceType

CloseEventCallback = Callable[["CalculatorSubWindow", QCloseEvent | None], None]


class CalculatorSubWindow(NodeEditorWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.set_title()

        self.scene.add_has_been_modified_listener(self.set_title)

        self._close_event_listeners: list[ReferenceType[CloseEventCallback]] = []

    def set_title(self):
        self.setWindowTitle(self.get_user_friendly_filename())

    def add_close_event_listener(self, callback: CloseEventCallback) -> None:
        """
        Add a new callback to be called when the scene is modified.

        :param callback: A callback function
        :type callback: Callable[[], None]
        """
        self._close_event_listeners.append(ref(callback))

    @override
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        for callback_ref in self._close_event_listeners:
            if callback := callback_ref():
                callback(self, a0)
