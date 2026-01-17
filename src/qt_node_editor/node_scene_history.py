"Maintain history of user actions."
import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager
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
    "History step data structure."
    desc: str  #: Step description
    snapshot: 'SceneSerialize'  #: Serialized scene
    selection: HistorySel  #: List of selected objects on the scene


class SceneHistory:
    """
    Support for undo/redo operations on the scene.

    Events
    ------
    - `History Modified` - a history stamp has been stored or restored
    - `History Stored` - a history stamp has been stored
    - `History Restored` - a history stamp has been restored
    """

    def __init__(self, scene: "Scene") -> None:
        """
        Initialize :class:`SceneHistory`.

        :param scene: Reference to a :class:`.Scene` instance
        """
        self.scene = scene  #: Reference to a :class:`.Scene` instance
        self.clear()
        self.history_limit = 32  #: Number of history steps that can be stored
        self._transaction = False
        # listeners
        self._history_modified_listeners: list[ReferenceType[Callable[[], None]]] = []
        self._history_stored_listeners: list[ReferenceType[Callable[[], None]]] = []
        self._history_restored_listeners: list[ReferenceType[Callable[[], None]]] = []

    def clear(self) -> None:
        "Initialize history stack."
        self.history_stack: list[HistoryStamp] = []
        self.history_current_step = -1
        self._history_modified_step: int | None = None

    def store_initial_history_stamp(self) -> None:
        "Save the first history step (on new file or file open)."
        self.store_history("Initial history stamp", modified=False)

    def add_history_modified_listener(self, callback: Callable[[], None]) -> None:
        """
        Add a new callback to be called when the scene history is updated.

        :param callback: A callback function
        :type callback: Callable[[], None]
        """
        self._history_modified_listeners.append(ref(callback))

    def add_history_stored_listener(self, callback: Callable[[], None]) -> None:
        """
        Add a new callback to be called when the scene history is updated.

        :param callback: A callback function
        :type callback: Callable[[], None]
        """
        self._history_stored_listeners.append(ref(callback))

    def add_history_restored_listener(self, callback: Callable[[], None]) -> None:
        """
        Add a new callback to be called when the scene history is updated.

        :param callback: A callback function
        :type callback: Callable[[], None]
        """
        self._history_restored_listeners.append(ref(callback))

    def can_undo(self) -> bool:
        "Undo action is available."
        return self.history_current_step > 0

    def can_redo(self) -> bool:
        "Redo action is available."
        return self.history_current_step + 1 < len(self.history_stack)

    def undo(self) -> None:
        "Undo last operation."
        log.debug("UNDO")
        if self.can_undo():
            self.history_current_step -= 1
            self._restore_history()

    def redo(self) -> None:
        "Redo next operation in history stack."
        log.debug("REDO")
        if self.can_redo():
            self.history_current_step += 1
            self._restore_history()

    def _restore_history(self) -> None:
        "Update the scene with the history stamp at current step."
        log.debug("Restoring history .... current_step @%d (%d)",
                  self.history_current_step, len(self.history_stack))
        self.restore_history_stamp(self.history_stack[self.history_current_step])
        self.scene.has_been_modified = self._history_modified_step is not None and \
            self.history_current_step >= self._history_modified_step
        for callback_ref in self._history_modified_listeners:
            if callback := callback_ref():
                callback()
        for callback_ref in self._history_restored_listeners:
            if callback := callback_ref():
                callback()

    @contextmanager
    def transaction(self, desc: str, *, modified: bool,
                    ) -> Iterator["SceneHistory"]:
        """
        Store history single time on exit from context manager.

        :param desc: New history step description
        :param modified: ``True`` if operation modifies the document
        :return: self
        """
        self._transaction = True
        yield self
        self._transaction = False
        self.store_history(desc, modified=modified)

    def store_history(self, desc: str, *, modified: bool) -> None:
        """
        Store new history step in the history stack.

        Triggers "history modified", "history stored" callbacks.

        :param desc: New history step description
        :param modified: ``True`` if operation modifies the document
        """
        if self._transaction:
            log.debug('Skip storing "%s" in history transaction mode', desc)
            return
        self.scene.has_been_modified = self.scene.has_been_modified or modified
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
            if self._history_modified_step is not None and \
                    self._history_modified_step > len(self.history_stack) - 1:
                self._history_modified_step = None

        if self.history_current_step + 1 >= self.history_limit:
            # history is full, remove the oldest item
            self.history_stack = self.history_stack[1:]  # FIXME: pop?
            self.history_current_step -= 1
            if self._history_modified_step is not None:
                self._history_modified_step = max(0, self._history_modified_step - 1)

        self.history_stack.append(hs)
        self.history_current_step += 1
        if modified and self._history_modified_step is None:
            self._history_modified_step = self.history_current_step
        log.debug("  -- setting step to: %d", self.history_current_step)

        # always trigger history modified callbacks (i.e. to update Edit menu)
        for callback_ref in self._history_modified_listeners:
            if callback := callback_ref():
                callback()
        for callback_ref in self._history_stored_listeners:
            if callback := callback_ref():
                callback()

    def create_history_stamp(self, desc: str) -> HistoryStamp:
        """
        Serialize current scene state into a new :class:`HistoryStamp` object.

        :param desc: DescriptNew history step descriptionion
        :return: Scene state serialized into a :class:`HistoryStamp` object
        """
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

    def restore_history_stamp(self, history_stamp: HistoryStamp) -> None:
        """
        Restore scene state from a :class:`HistoryStamp` object.

        :param history_stamp: a :class:`HistoryStamp` object to restore
        """
        log.debug("RHS: %s", history_stamp['desc'])
        with self.scene.selection_handling_disabled():
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

    def __del__(self) -> None:
        log.debug("delete history helper")
