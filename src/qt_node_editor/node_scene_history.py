import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qt_node_editor.node_scene import Scene

log = logging.getLogger(__name__)


class SceneHistory:
    def __init__(self, scene: "Scene") -> None:
        self.scene = scene
        self.history_stack = []
        self.history_current_step = -1
        self.history_limit = 8

    def undo(self):
        log.debug("UNDO")
        if self.history_current_step > 0:
            self.history_current_step -= 1
            self.restore_history()

    def redo(self):
        log.debug("REDO")
        if self.history_current_step + 1 < len(self.history_stack):
            self.history_current_step += 1
            self.restore_history()

    def restore_history(self):
        log.debug("Restoring history .... current_step @%d (%d)",
                  self.history_current_step, len(self.history_stack))
        self.restory_history_stamp(self.history_stack[self.history_current_step])

    def store_history(self, desc):
        log.debug('Storing history "%s" .... current_step @%d (%d)',
                  desc, self.history_current_step, len(self.history_stack))
        if self.history_current_step + 1 < len(self.history_stack):
            # history cursor is not at the end: destroy history steps to the right
            self.history_stack = self.history_stack[:self.history_current_step + 1]

        if self.history_current_step + 1 >= self.history_limit:
            # history is full, remove the oldest item
            self.history_stack = self.history_stack[1:]  # FIXME: pop?
            self.history_current_step -= 1

        hs = self.create_history_stamp(desc)

        self.history_stack.append(hs)
        self.history_current_step += 1
        log.debug("  -- setting step to: %d", self.history_current_step)

    def create_history_stamp(self, desc):
        return desc

    def restory_history_stamp(self, history_stamp):
        log.debug("RHS: %s", history_stamp)
