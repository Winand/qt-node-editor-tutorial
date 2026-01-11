"""
A module containing base class for Node's content graphical representation.

It also contains an example of overriden Text Widget which can pass to its
parent notification about currently being modified.
"""
import logging
from typing import TYPE_CHECKING, TypedDict, cast, override

from qtpy.QtGui import QFocusEvent
from qtpy.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget

from qt_node_editor.node_serializable import Serializable, SerializableMap

if TYPE_CHECKING:
    from qt_node_editor.node_node import Node

log = logging.getLogger(__name__)

class ContentSerialize(TypedDict):
    "Structure of serialized data for the default QDMContentWidget (empty)."


class QDMContentWidget[N: "Node"](QWidget, Serializable):
    """
    Base class for representation of the Node's graphics content.

    This class also provides layout for other widgets inside of a
    :py:class:`~qt_node_editor.node_node.Node`
    """

    def __init__(self, node: N, parent: QWidget | None = None) -> None:
        """
        Init :class:`QDMContentWidget`.

        :param node: reference to the `Node` object or its subclass
        :type node: Node
        :param parent: parent widget
        :type parent: QWidget | None

        :Instance Attributes:
            - **node** - reference to the :class:`.Node`
        """
        self.node = node
        super().__init__(parent)

        self.init_ui()

    def init_ui(self):
        """
        Set up layout and widgets to be rendered in graphics node class.

        See also :class:`~qt_node_editor.node_graphics_node.QDMGraphicsNode`.
        Called on init automatically.
        """
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)  # no space around contents
        self.setLayout(self._layout)

        self.wdg_label = QLabel("Some Title")
        self._layout.addWidget(self.wdg_label)
        self._layout.addWidget(QDMTextEdit("foo"))

    def set_editing_flag(self, value: bool):
        """
        Set editing flag in :class:`~qt_node_editor.node_graphics_view.QDMGraphicsView`.

        This flag helps to handle keys inside nodes with ``QLineEdit`` or ``QTextEdit``
        (overriden :py:class:`QDMTextEdit` class can be used)
        and with QGraphicsView class method ``keyPressEvent``.

        .. note::
            If you are handling key press events by default Qt Window's shortcuts
            and ``QAction``, you will not probably need to use this method
        """
        # FIXME: flag is set on the 1st view
        self.node.scene.get_view().editing_flag = value

    @override
    def serialize(self) -> ContentSerialize:
        return {

        }

    @override
    def deserialize(self, data: ContentSerialize, hashmap: SerializableMap, *,
                    restore_id: bool = True) -> bool:
        return True


class QDMTextEdit(QTextEdit):
    """Overriden ``QTextEdit`` widget which sends notification about being edited.

    Notification is sent via :meth:`QDMContentWidget.set_editing_flag`.

    .. note::
        This is an example of ``QTextEdit`` modification to be able to handle `Del` key
        with overriden ``keyPressEvent`` (without using ``QAction`` in menu or toolbar)
    """

    # FIXME: do not set editing flag from within text box (?)
    def focusInEvent(self, e: QFocusEvent) -> None:
        """
        Process focus event. Set editing flag in the scene view.

        :param e: Qt's focus event
        :type e: QFocusEvent
        """
        cast(QDMContentWidget, self.parentWidget()).set_editing_flag(True)
        return super().focusInEvent(e)

    def focusOutEvent(self, e: QFocusEvent | None) -> None:
        """
        Process focus out event. Unset editing flag in the scene view.

        :param e: Qt's focus event
        :type e: QFocusEvent
        """
        cast(QDMContentWidget, self.parentWidget()).set_editing_flag(False)
        return super().focusOutEvent(e)
