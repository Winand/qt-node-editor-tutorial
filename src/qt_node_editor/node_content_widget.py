"""
Content of a node (widgets)
"""
from qtpy.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget


class QDMContentWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.init_ui()

    def init_ui(self):
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)  # no space around contents
        self.setLayout(self._layout)

        self.wdg_label = QLabel("Some Title")
        self._layout.addWidget(self.wdg_label)
        self._layout.addWidget(QTextEdit("foo"))
