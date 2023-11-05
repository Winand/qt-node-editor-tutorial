import logging
from enum import Enum, auto

from qtpy.QtCore import QEvent, QPointF, Qt
from qtpy.QtGui import QKeyEvent, QMouseEvent, QPainter, QWheelEvent
from qtpy.QtWidgets import QGraphicsItem, QGraphicsView, QWidget

from qt_node_editor.node_edge import Edge, EdgeType
from qt_node_editor.node_graphics_edge import QDMGraphicsEdge
from qt_node_editor.node_graphics_node import QDMGraphicsNode
from qt_node_editor.node_graphics_socket import QDMGraphicsSocket
from qt_node_editor.node_scene import Scene

RenderHint = QPainter.RenderHint
log = logging.getLogger(__name__)

class Mode(Enum):
    NOOP = auto()
    EDGE_DRAG = auto()

EDGE_DRAG_START_THRESHOLD = 10  # px


class QDMGraphicsView(QGraphicsView):
    def __init__(self, scene: Scene, parent: QWidget | None):
        super().__init__(parent)
        self._scene = scene

        self.init_ui()
        self.setScene(scene.gr_scene)

        self.mode = Mode.NOOP
        self.editing_flag = False
        self.last_lmb_click_scene_pos = QPointF()

        self.zoom_in_factor = 1.25
        self.zoom_clamp = True
        self.zoom = 10
        self.zoom_step = 1
        self.zoom_range = range(0, 10)

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
        log.debug("LMB Click on %s %s", item, self.debug_modifiers(event))

        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            # Use Shift to select graphics items along with Ctrl
            self.modify_mouse_event(event, Qt.KeyboardModifier.ControlModifier)
            return

        if isinstance(item, QDMGraphicsSocket):
            if self.mode == Mode.NOOP:
                self.mode = Mode.EDGE_DRAG
                self.edge_drag_start(item)
                return

        if self.mode == Mode.EDGE_DRAG:
            if self.edge_drag_end(item):
                return

        super().mousePressEvent(event)  # pass to upper level

    def left_mouse_button_release(self, event: QMouseEvent):
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            # Use Shift to select graphics items along with Ctrl
            self.modify_mouse_event(event, Qt.KeyboardModifier.ControlModifier)
            return

        item = self.get_item_at_click(event)
        if self.mode == Mode.EDGE_DRAG:
            if self.distance_between_click_and_release_is_off(event):
                if self.edge_drag_end(item):
                    return
        super().mouseReleaseEvent(event)

    def middle_mouse_button_press(self, event: QMouseEvent):
        super().mousePressEvent(event)
        item = self.get_item_at_click(event)
        if log.getEffectiveLevel() == logging.DEBUG:
            if isinstance(item, QDMGraphicsEdge):
                print(f"MMB DEBUG: {item.edge}")
            elif isinstance(item, QDMGraphicsSocket):
                print(f"MMB DEBUG: {item.socket} has edge {item.socket.edge}")
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
        if self.mode == Mode.EDGE_DRAG:
            pos = self.mapToScene(event.pos())
            if not (self.drag_edge and self.drag_edge.gr_edge):
                # @Winand
                # edge_drag_start sets up drag_edge
                # Edge.remove sets gr_edge to None
                raise ValueError
            self.drag_edge.gr_edge.set_destination(pos.x(), pos.y())
            self.drag_edge.gr_edge.update()
        return super().mouseMoveEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete and not self.editing_flag:
            self.delete_selected()
        else:
            super().keyPressEvent(event)

    def delete_selected(self):
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
        self.previous_edge = item.socket.edge  # FIXME: last_start_socket is enough?
        self.last_start_socket = item.socket
        self.drag_edge = Edge(self._scene, item.socket, None, EdgeType.BEZIER)
        log.debug("  drag_edge: %s", self.drag_edge)

    def edge_drag_end(self, item: QGraphicsItem | None):
        "Return True if skip the rest of the code."
        self.mode = Mode.NOOP
        if not (self.drag_edge and self.drag_edge.gr_edge):
            # @Winand
            # edge_drag_start sets up drag_edge
            # Edge.remove sets gr_edge to None
            raise ValueError

        if isinstance(item, QDMGraphicsSocket) and \
                item.socket is not self.last_start_socket:
            log.debug("  previous_edge=%s", self.previous_edge)
            if item.socket.has_edge():
                item.socket.edge.remove()
            log.debug("  assign end socket %s", item.socket)
            if self.previous_edge is not None:
                self.previous_edge.remove()
            log.debug(" previous edge removed")
            self.drag_edge.start_socket = self.last_start_socket
            self.drag_edge.end_socket = item.socket
            self.drag_edge.start_socket.set_connected_edge(self.drag_edge)
            self.drag_edge.end_socket.set_connected_edge(self.drag_edge)
            log.debug(" reassigned start/end sockets to drag edge")
            self.drag_edge.update_positions()
            return True

        # Cancel:
        log.debug("End dragging edge")
        self.drag_edge.remove()
        self.drag_edge = None
        log.debug("about to set socket to previous edge: %s", self.previous_edge)
        if self.previous_edge is not None:
            if not self.previous_edge.start_socket:
                raise ValueError  # @Winand
            self.previous_edge.start_socket.edge = self.previous_edge
        log.debug("everything done.")
        return False
    
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
                     add_modifier: Qt.KeyboardModifier):
        "Add modifier key to the mouse event and call parent."
        event_type = event.type()
        event.ignore()
        new_event = QMouseEvent(
            event_type, event.position(), event.globalPosition(),
            event.button(), event.buttons() | Qt.MouseButton.LeftButton,
            event.modifiers() | add_modifier
        )
        if event_type == QEvent.Type.MouseButtonPress:
            super().mousePressEvent(new_event)
        elif event_type == QEvent.Type.MouseButtonRelease:
            super().mouseReleaseEvent(new_event)
        else:
            raise ValueError(f"Event {event_type} not supported")
