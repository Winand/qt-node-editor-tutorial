import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, override

from calc_conf import MIMETYPE_LISTBOX, Opcode, get_class_from_opcode
from qtpy.QtCore import Qt
from qtpy.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent, QPixmap
from qtpy.QtWidgets import QWidget
from util_datastream import from_bytearray

from qt_node_editor.node_editor_widget import NodeEditorWidget
from qt_node_editor.utils import ref, some

if TYPE_CHECKING:
    from weakref import ReferenceType

CloseEventCallback = Callable[["CalculatorSubWindow", QCloseEvent | None], None]

log = logging.getLogger(__name__)


class CalculatorSubWindow(NodeEditorWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.set_title()

        self.scene.add_has_been_modified_listener(self.set_title)
        self.scene.add_drag_enter_listener(self.on_drag_enter)
        self.scene.add_drop_listener(self.on_drop)

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

    def on_drag_enter(self, event: QDragEnterEvent) -> None:
        if some(event.mimeData()).hasFormat(MIMETYPE_LISTBOX):
            event.acceptProposedAction()  # also does setAccepted(True)
        else:
            event.ignore()  # =setAccepted(False)

    def on_drop(self, event: QDropEvent) -> None:
        mime_data = some(event.mimeData())
        if not mime_data.hasFormat(MIMETYPE_LISTBOX):
            event.ignore()
            return

        event.accept()
        event_data = mime_data.data(MIMETYPE_LISTBOX)
        _: tuple[QPixmap, Opcode, str] = from_bytearray(
            event_data, QPixmap, Opcode, str)
        _pixmap, opcode, text = _
        cursor_pos = event.position().toPoint()
        # TODO: pass QGraphicsView instance to listeners?
        scene_pos = self.scene.gr_scene.views()[0].mapToScene(cursor_pos)
        log.debug("GOT DROP: [%s] '%s' at %.1f,%.1f",
                  opcode.name, text, scene_pos.x(), scene_pos.y())

        node = get_class_from_opcode(opcode)(self.scene)
        node.set_pos(scene_pos.x(), scene_pos.y())
        self.scene.history.store_history(f"Created node {node.__class__.__name__}",
                                         modified=True)
