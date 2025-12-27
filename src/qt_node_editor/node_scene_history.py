import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, TypedDict

from qt_node_editor.node_graphics_edge import QDMGraphicsEdge
from qt_node_editor.node_graphics_node import QDMGraphicsNode
from qt_node_editor.node_serializable import SerializableID
from qt_node_editor.utils import ref

if TYPE_CHECKING:
    from weakref import ReferenceType

    from qt_node_editor.node_scene import Scene, SceneSerialize

log = logging.getLogger(__name__)

class HistorySel(TypedDict):
    "Selected nodes and edges."
    nodes: list[SerializableID]
    edges: list[SerializableID]

class HistoryStamp(TypedDict):
    desc: str
    snapshot: 'SceneSerialize'
    selection: HistorySel


class SceneHistory:
    def __init__(self, scene: "Scene") -> None:
        self.scene = scene
        self.clear()
        self.history_limit = 32
        self._history_modified_listeners: list[ReferenceType[Callable[[], None]]] = []

    def clear(self) -> None:
        "Initialize history stack."
        self.history_stack: list[HistoryStamp] = []
        self.history_current_step = -1

    def store_initial_history_stamp(self) -> None:
        self.store_history("Initial history stamp", modified=False)

    def can_undo(self) -> bool:
        "Undo action is available."
        return self.history_current_step > 0

    def can_redo(self) -> bool:
        "Redo action is available."
        return self.history_current_step + 1 < len(self.history_stack)

    def undo(self):
        log.debug("UNDO")
        if self.can_undo():
            self.history_current_step -= 1
            self.restore_history()

    def redo(self):
        log.debug("REDO")
        if self.can_redo():
            self.history_current_step += 1
            self.restore_history()

    def add_history_modified_listener(self, callback: Callable[[], None]) -> None:
        """
        Add a new callback to be called when the scene history is updated.

        :param callback: A callback function
        :type callback: Callable[[], None]
        """
        self._history_modified_listeners.append(ref(callback))

    def restore_history(self) -> None:
        "Update the scene with the history stamp at current step."
        log.debug("Restoring history .... current_step @%d (%d)",
                  self.history_current_step, len(self.history_stack))
        with self.scene.selection_handling_disabled():
            self.restore_history_stamp(self.history_stack[self.history_current_step])
        self.scene.has_been_modified = self.history_current_step > 0
        for callback_ref in self._history_modified_listeners:
            if callback := callback_ref():
                callback()

    def store_history(self, desc: str, *, modified: bool):
        self.scene.has_been_modified = modified
        hs = self.create_history_stamp(desc)
        if self.history_stack:  # @Winand
            hcs = self.history_stack[self.history_current_step]
            if hcs['snapshot'] == hs['snapshot'] and hcs['selection'] == hs['selection']:
                log.debug("History - no action")
                return
        log.debug('Storing history "%s" .... current_step @%d (%d)',
                  desc, self.history_current_step, len(self.history_stack))

        if self.history_current_step + 1 < len(self.history_stack):
            # history cursor is not at the end: destroy history steps to the right
            self.history_stack = self.history_stack[:self.history_current_step + 1]

        if self.history_current_step + 1 >= self.history_limit:
            # history is full, remove the oldest item
            self.history_stack = self.history_stack[1:]  # FIXME: pop?
            self.history_current_step -= 1

        self.history_stack.append(hs)
        self.history_current_step += 1
        log.debug("  -- setting step to: %d", self.history_current_step)

        # always trigger history modified callbacks (i.e. to update Edit menu)
        for callback_ref in self._history_modified_listeners:
            if callback := callback_ref():
                callback()

    def create_history_stamp(self, desc: str) -> HistoryStamp:
        sel_obj: HistorySel = {
            'nodes': [],
            'edges': [],
        }
        for item in self.scene.gr_scene.selectedItems():
            if isinstance(item, QDMGraphicsNode):
                sel_obj['nodes'].append(item.node.id)
            elif isinstance(item, QDMGraphicsEdge):
                sel_obj['edges'].append(item.edge.id)

        history_stamp: HistoryStamp = {
            'desc': desc,
            'snapshot': self.scene.serialize(),
            'selection': sel_obj,
        }
        return history_stamp

    def restore_history_stamp(self, history_stamp: HistoryStamp):
        log.debug("RHS: %s", history_stamp['desc'])

        self.scene.deserialize(history_stamp['snapshot'])

        for edge_id in history_stamp['selection']['edges']:
            for edge in self.scene.edges:
                if edge.id == edge_id:
                    edge.gr_edge.setSelected(True)
                    break

        for node_id in history_stamp['selection']['nodes']:
            for node in self.scene.nodes:
                if node.id == node_id:
                    node.gr_node.setSelected(True)
                    break
