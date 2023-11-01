from enum import Enum, auto

from qtpy.QtCore import QEvent, QPointF, Qt
from qtpy.QtGui import QMouseEvent, QPainter, QWheelEvent
from qtpy.QtWidgets import QGraphicsScene, QGraphicsView, QWidget

from qt_node_editor.node_graphics_socket import QDMGraphicsSocket

RenderHint = QPainter.RenderHint

class Mode(Enum):
    NOOP = auto()
    EDGE_DRAG = auto()

EDGE_DRAG_START_THRESHOLD = 10  # px


class QDMGraphicsView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, parent: QWidget | None):
        super().__init__(parent)
        self.gr_scene = scene

        self.init_ui()
        self.setScene(self.gr_scene)

        self.mode = Mode.NOOP
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
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def left_mouse_button_press(self, event: QMouseEvent):
        item = self.get_item_at_click(event)
        self.last_lmb_click_scene_pos = self.mapToScene(event.pos())
        if isinstance(item, QDMGraphicsSocket):
            if self.mode == Mode.NOOP:
                self.mode = Mode.EDGE_DRAG
                self.edge_drag_start()
                return

        if self.mode == Mode.EDGE_DRAG:
            if self.edge_drag_end(item):
                return

        super().mousePressEvent(event)  # pass to upper level

    def left_mouse_button_release(self, event: QMouseEvent):
        item = self.get_item_at_click(event)
        if self.mode == Mode.EDGE_DRAG:
            if self.distance_between_click_and_release_is_off(event):
                if self.edge_drag_end(item):
                    return
        super().mouseReleaseEvent(event)

    def middle_mouse_button_press(self, event: QMouseEvent):
        super().mousePressEvent(event)

    def middle_mouse_button_release(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)

    def get_item_at_click(self, event: QMouseEvent):
        "Return graphics item under cursor."
        pos = event.pos()
        obj = self.itemAt(pos)
        return obj

    def edge_drag_start(self):
        print("Start dragging edge")
        print("  assign Start Socket")

    def edge_drag_end(self, item):
        "Return True if skip the rest of the code."
        self.mode = Mode.NOOP
        print("End dragging edge")
        if isinstance(item, QDMGraphicsSocket):
            print("  assign end socket")
            return True
        return False
    
    def distance_between_click_and_release_is_off(self, event):
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
