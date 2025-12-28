from enum import IntEnum, auto
from pathlib import Path
from typing import override

from calc_conf import MIMETYPE_LISTBOX, Opcode
from qtpy.QtCore import QMimeData, QPoint, QSize, Qt
from qtpy.QtGui import QDrag, QIcon, QPixmap
from qtpy.QtWidgets import QListWidget, QListWidgetItem, QWidget
from util_datastream import to_bytearray


class Role(IntEnum):
    "Custom data roles for list items."
    Pixmap = Qt.ItemDataRole.UserRole
    Opcode = auto()


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
        self.add_item("Input", Path("icons/in.png"), Opcode.Input)
        self.add_item("Output", Path("icons/out.png"), Opcode.Output)
        self.add_item("Add", Path("icons/add.png"), Opcode.Add)
        self.add_item("Subtract", Path("icons/sub.png"), Opcode.Subtract)
        self.add_item("Multiply", Path("icons/mul.png"), Opcode.Multiply)
        self.add_item("Divide", Path("icons/divide.png"), Opcode.Divide)

    def add_item(self, name: str, icon: Path | None = None,
                 opcode: Opcode | None = None) -> None:
        item = QListWidgetItem(name, self)
        pixmap = QPixmap(str(Path(__file__).parent / icon) if icon else ".")
        item.setIcon(QIcon(pixmap))
        item.setSizeHint(QSize(32, 32))

        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
                      | Qt.ItemFlag.ItemIsDragEnabled)

        item.setData(Role.Pixmap, pixmap)
        if opcode:
            item.setData(Role.Opcode, opcode)

    @override
    def startDrag(self, supportedActions: Qt.DropAction) -> None:
        item = self.currentItem()
        assert item, "QDMDragListbox.startDrag: Current item is None"
        opcode: Opcode = item.data(Role.Opcode)

        pixmap = QPixmap(item.data(Role.Pixmap))
        mime_data = QMimeData()
        # mime_data.setText(item.text())
        mime_data.setData(MIMETYPE_LISTBOX,
            to_bytearray(pixmap, opcode, item.text()),
        )

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
        drag.setPixmap(pixmap)

        drag.exec(Qt.DropAction.MoveAction)
