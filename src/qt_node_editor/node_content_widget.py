"""
Content of a node (widgets)
"""
import logging
from typing import TYPE_CHECKING, TypedDict, cast

from qtpy.QtGui import QFocusEvent
from qtpy.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget

from qt_node_editor.node_serializable import Serializable

if TYPE_CHECKING:
    from qt_node_editor.node_graphics_view import QDMGraphicsView
    from qt_node_editor.node_node import Node

log = logging.getLogger(__name__)

class ContentSerialize(TypedDict):
    pass


class QDMContentWidget(QWidget, Serializable):
    def __init__(self, node: "Node", parent: QWidget | None = None):
        self.node = node
        super().__init__(parent)

        self.init_ui()

    def init_ui(self):
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)  # no space around contents
        self.setLayout(self._layout)

        self.wdg_label = QLabel("Some Title")
        self._layout.addWidget(self.wdg_label)
        self._layout.addWidget(QDMTextEdit("foo"))

    def set_editing_flag(self, value: bool):
        # FIXME: flag is set on the 1st view
        view = cast("QDMGraphicsView", self.node.scene.gr_scene.views()[0])
        view.editing_flag = value

    def serialize(self) -> ContentSerialize:
        return {

        }

    def deserialize(self, data: ContentSerialize, hashmap: dict = {}):
        return False


class QDMTextEdit(QTextEdit):
    # FIXME: do not set editing flag from within text box (?)
    def focusInEvent(self, e: QFocusEvent) -> None:
        cast(QDMContentWidget, self.parentWidget()).set_editing_flag(True)
        return super().focusInEvent(e)

    def focusOutEvent(self, e: QFocusEvent | None) -> None:
        cast(QDMContentWidget, self.parentWidget()).set_editing_flag(False)
        return super().focusOutEvent(e)
