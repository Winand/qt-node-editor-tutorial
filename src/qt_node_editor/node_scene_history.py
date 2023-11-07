import logging

from qt_node_editor.node_graphics_scene import Scene

log = logging.getLogger(__name__)


class SceneHistory:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.history_stack = []
        self.history_current_step = -1
        self.history_limit = 8

    def undo(self):
        log.debug("UNDO")

    def redo(self):
        log.debug("REDO")

    def restore_history(self):
        log.debug("Restoring history .... current_step @%d (%d)",
                  self.history_current_step, len(self.history_stack))
        self.restory_history_stamp(self.history_stack[self.history_current_step])

    def store_history(self, desc):
        log.debug("Storing history .... current_step @%d (%d)",
                  self.history_current_step, len(self.history_stack))
        hs = self.create_history_stamp(desc)

    def create_history_stamp(self, desc):
        return desc

    def restory_history_stamp(self, history_stamp):
        log.debug("RHS: %s", history_stamp)
