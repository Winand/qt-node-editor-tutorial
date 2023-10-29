from qtpy.QtCore import Qt, QEvent
from qtpy.QtGui import QPainter, QMouseEvent, QWheelEvent
from qtpy.QtWidgets import QGraphicsScene, QGraphicsView, QWidget

RenderHint = QPainter.RenderHint

class QDMGraphicsView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, parent: QWidget | None):
        super().__init__(parent)
        self.gr_scene = scene

        self.init_ui()
        self.setScene(self.gr_scene)

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
        return super().mousePressEvent(event)

    def left_mouse_button_release(self, event: QMouseEvent):
        return super().mouseReleaseEvent(event)

    def middle_mouse_button_press(self, event: QMouseEvent):
        return super().mousePressEvent(event)

    def middle_mouse_button_release(self, event: QMouseEvent):
        return super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        zoom_out_factor = 1 / self.zoom_in_factor
        if event.angleDelta().y() > 0:
            zoom_factor = self.zoom_in_factor
            self.zoom += self.zoom_step
        else:
            zoom_factor = zoom_out_factor
            self.zoom -= self.zoom_step
        
        clamped = False
        if self.zoom < self.zoom_range.start:
            self.zoom, clamped = self.zoom_range.start, True
        elif self.zoom > self.zoom_range.stop:
            self.zoom, clamped = self.zoom_range.stop, True
        if not clamped or not self.zoom_clamp:
            self.scale(zoom_factor, zoom_factor)
