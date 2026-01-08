import logging
from collections.abc import Callable
from enum import Enum, auto
from typing import TYPE_CHECKING, override

from qtpy.QtCore import QEvent, QPointF, Qt, Signal
from qtpy.QtGui import (
    QContextMenuEvent,
    QDragEnterEvent,
    QDropEvent,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QWheelEvent,
)
from qtpy.QtWidgets import QApplication, QGraphicsItem, QGraphicsView, QWidget

from qt_node_editor.node_edge import Edge, EdgeType
from qt_node_editor.node_graphics_cutline import QDMCutLine
from qt_node_editor.node_graphics_edge import QDMGraphicsEdge
from qt_node_editor.node_graphics_node import QDMGraphicsNode
from qt_node_editor.node_graphics_socket import QDMGraphicsSocket
from qt_node_editor.node_scene import Scene
from qt_node_editor.utils import ref

if TYPE_CHECKING:
    from weakref import ReferenceType

RenderHint = QPainter.RenderHint
log = logging.getLogger(__name__)

class ViewStateMode(Enum):
    NO_OP = auto()
    EDGE_DRAG = auto()
    EDGE_CUT = auto()

EDGE_DRAG_START_THRESHOLD = 10  # px

type WeakListener[T, R] = ReferenceType[Callable[[T], R]]


class QDMGraphicsView(QGraphicsView):
    scene_pos_changed = Signal(int, int)

    def __init__(self, scene: Scene, parent: QWidget | None):
        super().__init__(parent)
        self._scene = scene

        self.init_ui()
        self.setScene(scene.gr_scene)

        self.mode = ViewStateMode.NO_OP
        self.editing_flag = False
        self.rubber_band_dragging_rectangle = False
        self.last_lmb_click_scene_pos = QPointF()
        # False - viewport move detection on RMB press started, True - move detected
        self._viewport_scrolled: bool | None = None
        # call _empty_space_listeners once per one edge drag
        self._empty_space_handled: bool = True

        self.zoom_in_factor = 1.25
        self.zoom_clamp = True
        self.zoom = 10
        self.zoom_step = 1
        self.zoom_range = range(0, 10)

        # cutline (it's always in the scene but has no points by default)
        self.cutline = QDMCutLine()
        self._scene.gr_scene.addItem(self.cutline)

        self._drag_enter_listeners: list[WeakListener[QDragEnterEvent, None]] = []
        self._drop_listeners: list[WeakListener[QDropEvent, None]] = []
        self._empty_space_listeners: list[WeakListener[QMouseEvent, bool]] = []

    def init_ui(self):
        # https://doc.qt.io/qt-6/qpainter.html#RenderHint-enum
        # HighQualityAntialiasing is obsolete
        self.setRenderHints(RenderHint.Antialiasing |
                            RenderHint.TextAntialiasing |
                            RenderHint.SmoothPixmapTransform)
        # https://doc.qt.io/qt-6/qgraphicsview.html#ViewportUpdateMode-enum
        # Otherwise there are artifacts on scene background
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # https://doc.qt.io/qt-6/qgraphicsview.html#ViewportAnchor-enum
        # When zooming with `scale` use mouse position as anchor point
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Item selection rectangle
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        self.setAcceptDrops(True)

    @override
    def dragEnterEvent(self, event: QDragEnterEvent | None) -> None:
        assert event  # is never None
        for callback_ref in self._drag_enter_listeners:
            if callback := callback_ref():
                callback(event)

    @override
    def dropEvent(self, event: QDropEvent | None) -> None:
        assert event  # is never None
        for callback_ref in self._drop_listeners:
            if callback := callback_ref():
                callback(event)

    def add_drag_enter_listener(self, callback: Callable[[QDragEnterEvent], None],
                                ) -> None:
        self._drag_enter_listeners.append(ref(callback))

    def add_drop_listener(self, callback: Callable[[QDropEvent], None]) -> None:
        self._drop_listeners.append(ref(callback))

    def add_empty_space_listener(self, callback: Callable[[QMouseEvent], bool]) -> None:
        "Call listeners when edge is dragged to empty space."
        self._empty_space_listeners.append(ref(callback))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.left_mouse_button_press(event)
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.middle_mouse_button_press(event)
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_mouse_button_press(event)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.left_mouse_button_release(event)
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.middle_mouse_button_release(event)
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_mouse_button_release(event)
        else:
            super().mouseReleaseEvent(event)

    def right_mouse_button_press(self, event: QMouseEvent):
        # https://doc.qt.io/qt-6/qmouseevent-obsolete.html
        # event.modifiers - Ctrl, Shift, etc.
        # TODO: mouseReleaseEvent is not needed?
        if self.itemAt(event.pos()):  # if *not* clicked on an empty space
            super().mousePressEvent(event)
            return
        release_event = QMouseEvent(QEvent.Type.MouseButtonRelease,
                                    event.position(), event.globalPosition(),
                                    Qt.MouseButton.RightButton,
                                    Qt.MouseButton.NoButton, event.modifiers())
        super().mouseReleaseEvent(release_event)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        fake_event = QMouseEvent(event.type(), event.position(),
                                event.globalPosition(),
                                Qt.MouseButton.LeftButton,
                                event.buttons() | Qt.MouseButton.LeftButton,
                                event.modifiers())
        super().mousePressEvent(fake_event)
        self._viewport_scrolled = False  # start viewport move tracking

    def right_mouse_button_release(self, event: QMouseEvent):
        fake_event = QMouseEvent(event.type(), event.position(),
                                event.globalPosition(),
                                Qt.MouseButton.LeftButton,
                                event.buttons() & ~Qt.MouseButton.LeftButton,
                                event.modifiers())
        super().mouseReleaseEvent(fake_event)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

    def left_mouse_button_press(self, event: QMouseEvent):
        item = self.get_item_at_click(event)
        self.last_lmb_click_scene_pos = self.mapToScene(event.pos())
        # log.debug("LMB Click on %s %s", item, self.debug_modifiers(event))

        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            # Use Shift to select graphics items along with Ctrl
            event = self.modify_mouse_event(event,
                                        Qt.KeyboardModifier.ControlModifier,
                                        Qt.KeyboardModifier.ShiftModifier)

        if isinstance(item, QDMGraphicsSocket):
            if self.mode == ViewStateMode.NO_OP:
                self._empty_space_handled = False
                self.mode = ViewStateMode.EDGE_DRAG
                self.edge_drag_start(item)
                return

        if self.mode == ViewStateMode.EDGE_DRAG:
            if not item and not self._empty_space_handled:
                for callback_ref in self._empty_space_listeners:
                    if callback := callback_ref():
                        self._empty_space_handled = callback(event)
                if self._empty_space_handled:
                    return
            # TODO: if you click on the same pin you started to drag it doesn't
            # return and selects underlying edge or node. Return in both cases?
            if self.edge_drag_end(item):
                return

        if item is None:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Ctrl + background click
                self.mode  = ViewStateMode.EDGE_CUT
                fake_event = QMouseEvent(
                    QEvent.Type.MouseButtonRelease,
                    event.position(), event.globalPosition(),
                    Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton,
                    event.modifiers()
                )
                super().mouseReleaseEvent(fake_event)
                QApplication.setOverrideCursor(Qt.CursorShape.CrossCursor)
                self.cutline.line_points = []  # reset old line_points
                self.cutline.show()
                return
            # `rubberBandChanged` signal can be used but some flag is still needed
            # to distinguish rubber band release from click in mouse release event
            self.rubber_band_dragging_rectangle = True
            self._scene.set_selection_handling(enable=False)

        super().mousePressEvent(event)  # pass to upper level

    def left_mouse_button_release(self, event: QMouseEvent):
        print("RELEASE")
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            # Use Shift to select graphics items along with Ctrl
            event = self.modify_mouse_event(event,
                                        Qt.KeyboardModifier.ControlModifier,
                                        Qt.KeyboardModifier.ShiftModifier)

        item = self.get_item_at_click(event)
        if self.mode == ViewStateMode.EDGE_DRAG:
            if self.distance_between_click_and_release_is_off(event):
                handled = False
                if not item:
                    for callback_ref in self._empty_space_listeners:
                        if callback := callback_ref():
                            handled = callback(event)
                if handled or self.edge_drag_end(item):
                    return

        if self.mode == ViewStateMode.EDGE_CUT:
            self.cut_intersecting_edges()
            # keep `line_points` so boundingRect is on screen and cutline is hidden
            self.cutline.hide()
            QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
            self.mode = ViewStateMode.NO_OP
            return

        super().mouseReleaseEvent(event)

        # see also 24: https://youtu.be/FPP4RcGeQpU?t=1011
        # if self.mode != Mode.EDGE_DRAG:  # clicked on a pin to start edge dragging
        if self.rubber_band_dragging_rectangle:
            self.rubber_band_dragging_rectangle = False
            self._scene.set_selection_handling(enable=True)
            self._scene.gr_scene.selectionChanged.emit()
            # current_selected_items = self._scene.gr_scene.selectedItems()
            # if current_selected_items != self._scene.last_selected_items:
            #     if current_selected_items:
            #         self._scene.gr_scene.item_selected.emit()
            #     else:
            #         self._scene.gr_scene.items_deselected.emit()
            # return

    def middle_mouse_button_press(self, event: QMouseEvent):
        super().mousePressEvent(event)
        item = self.get_item_at_click(event)
        if log.getEffectiveLevel() == logging.DEBUG:
            if isinstance(item, QDMGraphicsEdge):
                print(f"MMB DEBUG: {item.edge}")
            elif isinstance(item, QDMGraphicsSocket):
                print(f"MMB DEBUG: {item.socket} has edge {item.socket.edges}")
            elif item is None:
                print('SCENE:')
                print('  Nodes:')
                for node in self._scene.nodes:
                    print(f'    {node}')
                print('  Edges:')
                for edge in self._scene.edges:
                    print(f'    {edge}')

    def middle_mouse_button_release(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.mode == ViewStateMode.EDGE_DRAG:
            pos = self.mapToScene(event.pos())
            if not (self.drag_edge and self.drag_edge.gr_edge):
                # @Winand
                # edge_drag_start sets up drag_edge
                # Edge.remove sets gr_edge to None
                raise ValueError
            self.drag_edge.gr_edge.set_destination(pos.x(), pos.y())

        if self.mode == ViewStateMode.EDGE_CUT:
            pos = self.mapToScene(event.pos())
            self.cutline.line_points.append(pos)
            self.cutline.update()

        self.last_scene_mouse_position = self.mapToScene(event.pos())

        self.scene_pos_changed.emit(
            int(self.last_scene_mouse_position.x()),
            int(self.last_scene_mouse_position.y()),
        )

        return super().mouseMoveEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # if event.key() == Qt.Key.Key_Delete and not self.editing_flag:
        #     self.delete_selected()
        # elif event.key() == Qt.Key.Key_S and \
        #         event.modifiers() & Qt.KeyboardModifier.ControlModifier:
        #     self._scene.save_to_file("graph.json")
        # elif event.key() == Qt.Key.Key_L and \
        #         event.modifiers() & Qt.KeyboardModifier.ControlModifier:
        #     self._scene.load_from_file("graph.json")
        # elif event.key() == Qt.Key.Key_Z and \
        #         event.modifiers() & Qt.KeyboardModifier.ControlModifier:
        #     self._scene.history.undo()
        # elif event.key() == Qt.Key.Key_Y and \
        #         event.modifiers() & Qt.KeyboardModifier.ControlModifier:
        #     self._scene.history.redo()
        # elif event.key() == Qt.Key.Key_H:
        #     print(f"HISTORY len({len(self._scene.history.history_stack)})"
        #           f" -- current_step {self._scene.history.history_current_step}")
        #     for ix, item in enumerate(self._scene.history.history_stack):
        #         print(f"# {ix} -- {item['desc']}")
        # else:
        super().keyPressEvent(event)
    
    def cut_intersecting_edges(self):  # TODO: item.collidesWith? then shape is required
        for ix in range(len(self.cutline.line_points) - 1):
            p1 = self.cutline.line_points[ix]
            p2 = self.cutline.line_points[ix + 1]

            for edge in self._scene.edges:
                if edge.gr_edge.intersects_with(p1, p2):
                    edge.remove()
        self._scene.history.store_history("Delete cut edges", modified=True)

    def delete_selected(self):
        with self._scene.history.transaction("Delete selected", modified=True):
            for item in self._scene.gr_scene.selectedItems():
                if isinstance(item, QDMGraphicsEdge):
                    item.edge.remove()
                elif isinstance(item, QDMGraphicsNode):
                    item.node.remove()

    def debug_modifiers(self, event: QMouseEvent):
        out = "MODS: "
        modifiers = event.modifiers()
        for mod in Qt.KeyboardModifier:
            if mod != Qt.KeyboardModifier.KeyboardModifierMask and modifiers & mod:
                out += f"{mod.name.split('Modifier')[0]} "
        return out

    def get_item_at_click(self, event: QMouseEvent):
        "Return graphics item under cursor."
        pos = event.pos()
        obj = self.itemAt(pos)
        return obj

    def edge_drag_start(self, item: QDMGraphicsSocket):
        log.debug("Start dragging edge")
        log.debug("  assign Start Socket to: %s", item.socket)
        # self.previous_edge = item.socket.edges  # FIXME: last_start_socket is enough?
        self.drag_start_socket = item.socket
        self.drag_edge = Edge(self._scene, item.socket, None, EdgeType.BEZIER)
        log.debug("  drag_edge: %s", self.drag_edge)

    def edge_drag_end(self, item: QGraphicsItem | None) -> Edge | None:
        "Create a new Edge and connect to `item` if it is a socket."
        self.mode = ViewStateMode.NO_OP
        if not (self.drag_edge and self.drag_edge.gr_edge):
            # @Winand
            # edge_drag_start sets up drag_edge
            # Edge.remove sets gr_edge to None
            raise ValueError
        log.debug("End dragging edge")
        self.drag_edge.remove()
        self.drag_edge = None

        if isinstance(item, QDMGraphicsSocket) and \
                item.socket is not self.drag_start_socket:
            # if we release dragging on a socket other than the start socket
            # log.debug("  previous_edge=%s", self.previous_edge)

            # if item.socket.has_edge():
            #     item.socket.edges.remove()

            if not item.socket.is_multi_edges:  # clear target socket if needed
                item.socket.remove_all_edges()
            if not self.drag_start_socket.is_multi_edges:  # clear start socket
                self.drag_start_socket.remove_all_edges()

            # log.debug("  assign end socket %s", item.socket)
            # if self.previous_edge is not None:
            #     self.previous_edge.remove()
            # log.debug(" previous edge removed")
            # self.drag_edge.start_socket = self.drag_start_socket
            # self.drag_edge.end_socket = item.socket
            # self.drag_edge.start_socket.add_edge(self.drag_edge)
            # self.drag_edge.end_socket.add_edge(self.drag_edge)
            # log.debug(" reassigned start/end sockets to drag edge")
            # self.drag_edge.update_positions()

            new_edge = Edge(self._scene, self.drag_start_socket, item.socket, EdgeType.BEZIER)
            log.debug("created a new edge %s connecting %s <--> %s",
                      new_edge, new_edge.start_socket, new_edge.end_socket)

            self._scene.history.store_history("Created new edge by dragging",
                                              modified=True)

            for socket in [self.drag_start_socket, item.socket]:
                socket.node.on_edge_connection_changed(new_edge)
                if socket.is_input:
                    socket.node.on_input_data_changed(new_edge)

            return new_edge

        # Cancel:
        # log.debug("about to set socket to previous edge: %s", self.previous_edge)
        # if self.previous_edge is not None:
        #     if not self.previous_edge.start_socket:
        #         raise ValueError  # @Winand
        #     self.previous_edge.start_socket.edges = self.previous_edge
        log.debug("everything done.")
        return None
    
    def distance_between_click_and_release_is_off(self, event: QMouseEvent):
        "Measures if we are too far from the last LMB click scene position."
        new_lmb_release_scene_pos = self.mapToScene(event.pos())
        dist_scene = new_lmb_release_scene_pos - self.last_lmb_click_scene_pos
        return (dist_scene.x() ** 2 + dist_scene.y() ** 2) \
                > EDGE_DRAG_START_THRESHOLD**2

    def wheelEvent(self, event: QWheelEvent) -> None:
        y_delta = event.angleDelta().y()
        if y_delta > 0:
            zoom_factor = self.zoom_in_factor
            self.zoom += self.zoom_step
        elif y_delta < 0:
            zoom_out_factor = 1 / self.zoom_in_factor
            zoom_factor = zoom_out_factor
            self.zoom -= self.zoom_step
        else: # horizontal scroll
            # FIXME: not very precise when scrolling back and forth
            center = self.mapToScene(self.rect()).boundingRect().center()
            self.centerOn(center.x() - event.angleDelta().x(), center.y())
            return

        clamped = False
        if self.zoom < self.zoom_range.start:
            self.zoom, clamped = self.zoom_range.start, True
        elif self.zoom > self.zoom_range.stop:
            self.zoom, clamped = self.zoom_range.stop, True
        if not clamped or not self.zoom_clamp:
            self.scale(zoom_factor, zoom_factor)

    # @Winand
    def modify_mouse_event(self, event: QMouseEvent,
                     add_modifier: Qt.KeyboardModifier,
                     rem_modifier: Qt.KeyboardModifier):
        "Add modifier key to the mouse event and call parent."
        event_type = event.type()
        event.ignore()
        new_event = QMouseEvent(
            event_type, event.position(), event.globalPosition(),
            event.button(), event.buttons() | Qt.MouseButton.LeftButton,
            event.modifiers() | add_modifier & ~rem_modifier
        )
        return new_event
        # if event_type == QEvent.Type.MouseButtonPress:
        #     super().mousePressEvent(new_event)
        # elif event_type == QEvent.Type.MouseButtonRelease:
        #     super().mouseReleaseEvent(new_event)
        # else:
        #     raise ValueError(f"Event {event_type} not supported")

    @override
    def scrollContentsBy(self, dx: int, dy: int) -> None:
        "Event called on every viewport scroll."
        if self._viewport_scrolled is False:
            self._viewport_scrolled = True
        super().scrollContentsBy(dx, dy)

    @override
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:  # type: ignore[reportIncompatibleMethodOverride]
        "Do not propagate context menu event if the viewport was scrolled with RMB."
        if self._viewport_scrolled:  # viewport moved
            self._viewport_scrolled = None
            event.accept()
            return
        super().contextMenuEvent(event)

    def __del__(self) -> None:
        log.debug("delete graphics view")
