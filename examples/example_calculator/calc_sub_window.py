import logging
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, cast, override

from calc_conf import CALC_NODES, MIMETYPE_LISTBOX, Opcode, get_class_from_opcode
from calc_node_base import CalcNode, CalcNodeSerialize
from qtpy.QtCore import Qt
from qtpy.QtGui import (
    QAction,
    QCloseEvent,
    QContextMenuEvent,
    QDragEnterEvent,
    QDropEvent,
    QPixmap,
)
from qtpy.QtWidgets import QGraphicsProxyWidget, QGraphicsTextItem, QMenu, QWidget
from util_datastream import from_bytearray

from qt_node_editor.node_content_widget import QDMContentWidget
from qt_node_editor.node_edge import Edge, EdgeType
from qt_node_editor.node_editor_widget import NodeEditorWidget
from qt_node_editor.node_graphics_edge import QDMGraphicsEdge
from qt_node_editor.node_graphics_node import QDMGraphicsNode
from qt_node_editor.node_graphics_socket import QDMGraphicsSocket
from qt_node_editor.node_node import Node, NodeSerialize
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

        self.init_new_node_actions()

        self.scene.add_has_been_modified_listener(self.set_title)
        self.scene.add_drag_enter_listener(self.on_drag_enter)
        self.scene.add_drop_listener(self.on_drop)
        self.scene.set_node_class_selector(self.get_node_type)

        self._close_event_listeners: list[ReferenceType[CloseEventCallback]] = []

    def get_node_type(self, data: NodeSerialize) -> type[CalcNode] | None:
        "Retrieve custom node class from serialized node."
        data = cast(CalcNodeSerialize, data)
        if "opcode" in data:
            return CALC_NODES[data["opcode"]]
        return None

    @override
    def load_file(self, filename: Path) -> bool:
        if super().load_file(filename):
            for node in cast(list[CalcNode], self.scene.nodes):
                if node.opcode == Opcode.Output:
                    node.eval()
            return True
        return False

    def init_new_node_actions(self):
        self.node_actions = {
            node.opcode: QAction(node.get_icon(), node.optitle)
            for node in CALC_NODES.values()
        }
        for opcode, action in self.node_actions.items():
            action.setData(opcode)

    def init_nodes_context_menu(self) -> QMenu:
        context_menu = QMenu(self)
        for _, action in sorted(self.node_actions.items()):
            context_menu.addAction(action)
        return context_menu

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
        scene_pos = self.scene.get_view().mapToScene(cursor_pos)
        log.debug("GOT DROP: [%s] '%s' at %.1f,%.1f",
                  opcode.name, text, scene_pos.x(), scene_pos.y())

        node = get_class_from_opcode(opcode)(self.scene)
        node.set_pos(scene_pos.x(), scene_pos.y())
        self.scene.history.store_history(f"Created node {node.__class__.__name__}",
                                         modified=True)

    @override
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:  # type: ignore[reportIncompatibleMethodOverride]
        item = self.scene.get_item_at(event.pos())
        if isinstance(item, QGraphicsProxyWidget):
            item = cast(QDMContentWidget, item.widget()).node.gr_node
        elif isinstance(item, QDMGraphicsSocket) or \
            (isinstance(item, QGraphicsTextItem) and item.objectName() == "title"):
            item = item.parentItem()
        log.debug(item)

        if isinstance(item, QDMGraphicsNode):
            self.handle_node_context_menu(event, item.node)
        elif isinstance(item, QDMGraphicsEdge):
            self.handle_edge_context_menu(event, item.edge)
        else:
            self.handle_new_node_context_menu(event)
        return super().contextMenuEvent(event)

    def handle_node_context_menu(self, event: QContextMenuEvent, node: Node) -> None:
        context_menu = QMenu(self)
        act_mark_dirty = context_menu.addAction("Mark Dirty")
        act_mark_desc_dirty = context_menu.addAction("Mark Descendants Dirty")
        act_mark_invalid = context_menu.addAction("Mark Invalid")
        act_unmark_invalid = context_menu.addAction("Unmark Invalid")
        act_eval = context_menu.addAction("Eval")

        action = context_menu.exec(self.mapToGlobal(event.pos()))
        if action:
            log.info("Action %s on node %s", action.text(), node.title)

        if action == act_mark_dirty:
           node.mark_dirty()
        elif action == act_mark_desc_dirty:
           node.mark_descendants_dirty()
        elif action == act_mark_invalid:
           node.mark_invalid()
        elif action == act_unmark_invalid:
           node.mark_invalid(unset=True)
        elif action == act_eval:
           val = node.eval()
           log.info("EVALUATED: %s", val)

    def handle_edge_context_menu(self, event: QContextMenuEvent, edge: Edge) -> None:
        context_menu = QMenu(self)
        act_bezier = context_menu.addAction("Bezier Edge")
        act_direct = context_menu.addAction("Direct Edge")

        action = context_menu.exec(self.mapToGlobal(event.pos()))
        if action == act_bezier:
           edge.edge_type = EdgeType.BEZIER
        elif action == act_direct:
           edge.edge_type = EdgeType.DIRECT

    def handle_new_node_context_menu(self, event: QContextMenuEvent) -> None:
        context_menu = self.init_nodes_context_menu()
        if not (action := context_menu.exec(self.mapToGlobal(event.pos()))):
            return
        new_calc_node = get_class_from_opcode(action.data())(self.scene)
        scene_pos = self.scene.get_view().mapToScene(event.pos())
        new_calc_node.set_pos(scene_pos.x(), scene_pos.y())
        new_calc_node.gr_node.setSelected(True)
        log.debug("Selected node: %s", new_calc_node)
