from pathlib import Path

from qtpy.QtCore import QSize, Qt
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import QListWidget, QListWidgetItem, QWidget


class QDMDragListbox(QListWidget):
    "List widget with draggable items with icons."

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        self.setIconSize(QSize(32, 32))
        self.setSelectionMode(self.SelectionMode.SingleSelection)
        self.setDragEnabled(True)
        self.add_items()

    def add_items(self) -> None:
        self.add_item("Input", Path("icons/in.png"))
        self.add_item("Output", Path("icons/out.png"))
        self.add_item("Add", Path("icons/add.png"))
        self.add_item("Subtract", Path("icons/sub.png"))
        self.add_item("Multiply", Path("icons/mul.png"))
        self.add_item("Divide", Path("icons/divide.png"))

    def add_item(self, name: str, icon: Path | None = None, op_code: int = 0) -> None:
        item = QListWidgetItem(name, self)
        pixmap = QPixmap(str(Path(__file__).parent / icon) if icon else ".")
        item.setIcon(QIcon(pixmap))
        item.setSizeHint(QSize(32, 32))

        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDragEnabled)

        item.setData(Qt.ItemDataRole.UserRole, pixmap)
        item.setData(Qt.ItemDataRole.UserRole + 1, op_code)

