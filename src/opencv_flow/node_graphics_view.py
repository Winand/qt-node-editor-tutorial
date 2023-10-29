from qtpy.QtCore import Qt
from qtpy.QtGui import QPainter
from qtpy.QtWidgets import QGraphicsScene, QGraphicsView, QWidget

RenderHint = QPainter.RenderHint

class QDMGraphicsView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, parent: QWidget | None):
        super().__init__(parent)
        self.gr_scene = scene

        self.init_ui()
        self.setScene(self.gr_scene)

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