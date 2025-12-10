from collections.abc import Callable
from typing import override

from qtpy.QtCore import Qt
from qtpy.QtGui import QCloseEvent, QKeySequence
from qtpy.QtWidgets import (
    QDockWidget,
    QListWidget,
    QMdiArea,
    QMdiSubWindow,
    QMenuBar,
    QMessageBox,
    QStatusBar,
)

from qt_node_editor.node_editor_window import NodeEditorWindow
from qt_node_editor.utils import some


class CalculatorWindow(NodeEditorWindow):
    statusBar: Callable[[], QStatusBar]  # type: ignore[reportIncompatibleMethodOverride] # noqa: N815
    menuBar: Callable[[], QMenuBar]  # type: ignore[reportIncompatibleMethodOverride] # noqa: N815
    # def __init__(self, parent: QWidget | None = None) -> None:
    #     super().__init__(parent)
    #     self.init_ui()

    def init_ui(self) -> None:
        self.name_company = "Winand"
        self.name_product = "Calculator NodeEditor"

        self.mdi_area = QMdiArea()
        self.mdi_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mdi_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mdi_area.setViewMode(QMdiArea.ViewMode.TabbedView)
        self.mdi_area.setDocumentMode(True)
        self.mdi_area.setTabsClosable(True)
        self.mdi_area.setTabsMovable(True)
        self.setCentralWidget(self.mdi_area)

        self.mdi_area.subWindowActivated.connect(self.update_menus)
        # self.window_mapper = QSignalMapper(self)
        # self.window_mapper.mapping(QWidget).connect(self.set_active_subwindow)

        self.create_menus()
        self.create_toolbars()
        self.create_statusbar()
        self.update_menus()

        self.create_nodes_dock()

        self.read_settings()

        self.setWindowTitle("Calculator NodeEditor Example")

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        self.mdi_area.closeAllSubWindows()
        if self.mdi_area.currentSubWindow():
            event.ignore()
        else:
            self.write_settings()
            event.accept()

    def update_menus(self) -> None:
        ...

    def about(self) -> None:
        QMessageBox.about(self, "About Calculator NodeEditor Example",
            "The <b>Calculator NodeEditor</b> example demonstrates how to write "
            "multiple document interface applications using Qt and NodeEditor.")

    def create_menus(self) -> None:
        super().create_menus()

        self.menu_window = some(self.menuBar().addMenu("&Window"))
        self.update_menu_window()
        self.menu_window.aboutToShow.connect(self.update_menu_window)

        self.menuBar().addSeparator()

        self.menu_help = some(self.menuBar().addMenu("&Help"))
        self.menu_help.addAction(self.create_act(
            "&About", self.about, tooltip="Show the application's About box"))

    def update_menu_window(self) -> None:
        "Create Window menu with a list of currently opened documents."
        self.menu_window.clear()
        self.menu_window.addAction(self.create_act(
            "Cl&ose", self.mdi_area.closeActiveSubWindow,
            tooltip="Close the active window"))
        self.menu_window.addAction(self.create_act(
            "Close &All", self.mdi_area.closeAllSubWindows,
            tooltip="Close all the windows"))
        self.menu_window.addSeparator()
        self.menu_window.addAction(self.create_act(
            "&Tile", self.mdi_area.tileSubWindows, tooltip="Tile the windows"))
        self.menu_window.addAction(self.create_act(
            "&Cascade", self.mdi_area.cascadeSubWindows, tooltip="Cascade the windows"))
        self.menu_window.addSeparator()
        self.menu_window.addAction(self.create_act(
            "Ne&xt", self.mdi_area.focusNextChild, QKeySequence.StandardKey.NextChild,
            "Move the focus to the next window"))
        self.menu_window.addAction(self.create_act(
            "Pre&vious", self.mdi_area.focusPreviousChild,
            QKeySequence.StandardKey.PreviousChild,
            "Move the focus to the previous window"))

        windows = self.mdi_area.subWindowList()
        if len(windows) > 0:
            self.menu_window.addSeparator()
        # for i, window in enumerate(windows):
        #     child = some(window.widget())
        #     text = "%d %s" % (i + 1, child.userFriendlyCurrentFile())


    def create_toolbars(self) -> None:
        ...

    def create_nodes_dock(self):
        self.list_widget = QListWidget()
        self.list_widget.addItems(["Add", "Substract", "Multiply", "Divide"])
        self.items = QDockWidget("Nodes")
        self.items.setWidget(self.list_widget)
        self.items.setFloating(False)

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.items)

    def create_statusbar(self) -> None:
        self.statusBar().showMessage("Ready")

    def set_active_subwindow(self, window: QMdiSubWindow | None):
        if window:
            self.mdi_area.setActiveSubWindow(window)
