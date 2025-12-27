from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import cast, override

import qss.nodeeditor_dark_resources  # noqa: F401 images for the dark skin
from calc_drag_listbox import QDMDragListbox
from calc_sub_window import CalculatorSubWindow
from qtpy.QtCore import Qt
from qtpy.QtGui import QCloseEvent, QIcon, QKeySequence, QPixmap
from qtpy.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QMdiArea,
    QMdiSubWindow,
    QMenuBar,
    QMessageBox,
    QStatusBar,
)

from qt_node_editor.node_editor_window import NodeEditorWindow
from qt_node_editor.utils import load_stylesheets, some


class CalculatorWindow(NodeEditorWindow):
    statusBar: Callable[[], QStatusBar]  # type: ignore[reportIncompatibleMethodOverride] # noqa: N815
    menuBar: Callable[[], QMenuBar]  # type: ignore[reportIncompatibleMethodOverride] # noqa: N815
    # def __init__(self, parent: QWidget | None = None) -> None:
    #     super().__init__(parent)
    #     self.init_ui()

    def init_ui(self) -> None:
        self.name_company = "Winand"
        self.name_product = "Calculator NodeEditor"

        self.stylesheet_filename = Path(__file__).parent / "qss/nodeeditor.qss"
        load_stylesheets(
            Path(__file__).parent / "qss/nodeeditor-dark.qss",
            self.stylesheet_filename,
        )

        # https://stackoverflow.com/a/31308534 | https://youtu.be/C29ftCo9h50?t=501
        self.empty_icon = QIcon(QPixmap(1, 1))

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

        self.create_nodes_dock()
        self.create_actions()
        self.create_menus()
        self.create_toolbars()
        self.create_statusbar()
        self.update_menus()

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

    @override
    def create_actions(self) -> None:
        super().create_actions()
        self.act_wnd_close = self.create_act(
            "Cl&ose", self.mdi_area.closeActiveSubWindow,
            tooltip="Close the active window")
        self.act_wnd_close_all = self.create_act(
            "Close &All", self.mdi_area.closeAllSubWindows,
            tooltip="Close all the windows")
        self.act_wnd_tile = self.create_act(
            "&Tile", self.mdi_area.tileSubWindows, tooltip="Tile the windows")
        self.act_wnd_cascade = self.create_act(
            "&Cascade", self.mdi_area.cascadeSubWindows, tooltip="Cascade the windows")
        self.act_wnd_next = self.create_act(
            "Ne&xt", self.mdi_area.focusNextChild, QKeySequence.StandardKey.NextChild,
            "Move the focus to the next window")
        self.act_wnd_prev = self.create_act(
            "Pre&vious", self.mdi_area.focusPreviousChild,
            QKeySequence.StandardKey.PreviousChild,
            "Move the focus to the previous window")

    @override
    def current_nodeeditor_widget(self) -> CalculatorSubWindow | None:
        "Return the current NodeEditorWidget instance."
        if active_subwindow := self.mdi_area.activeSubWindow():
            return cast(CalculatorSubWindow, active_subwindow.widget())
        return None


    @override
    def set_title(self, editor: CalculatorSubWindow | None = None) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        "Update tab title."
        if editor:
            editor.set_title()

    @override
    def on_file_new(self) -> None:
        sub_wnd = self.create_mdi_child()
        cast(CalculatorSubWindow, sub_wnd.widget()).new_file()
        sub_wnd.show()

    @override
    def on_file_open(self) -> None:
        fnames, _ = QFileDialog.getOpenFileNames(self, 'Open graph from file',
                                                 filter="JSON files (*.json)")
        for fname in filter(Path.is_file, map(Path, fnames)):
            if existing := self.find_mdi_child(fname):
                self.mdi_area.setActiveSubWindow(existing)
                continue
            nodeeditor = CalculatorSubWindow()
            if not nodeeditor.load_file(fname):
                nodeeditor.close()
                continue
            self.statusBar().showMessage(f"File {fname} loaded", 5000)
            nodeeditor.set_title()
            subwnd = self.create_mdi_child(nodeeditor)
            subwnd.show()

    def about(self) -> None:
        QMessageBox.about(self, "About Calculator NodeEditor Example",
            "The <b>Calculator NodeEditor</b> example demonstrates how to write "
            "multiple document interface applications using Qt and NodeEditor.")

    @override
    def create_menus(self) -> None:
        super().create_menus()

        # FIXME: edit actions become enable/disabled only when menu is shown
        self.menu_edit.aboutToShow.connect(self.update_menu_edit)

        self.menu_window = some(self.menuBar().addMenu("&Window"))
        self.update_menu_window()
        self.menu_window.aboutToShow.connect(self.update_menu_window)

        self.menu_help = some(self.menuBar().addMenu("&Help"))
        self.menu_help.addAction(self.create_act(
            "&About", self.about, tooltip="Show the application's About box"))

    def update_menus(self, window: QMdiSubWindow | None = None) -> None:
        "Disable some menu actions based on the presence of an active window."
        has_active_doc = window is not None
        self.act_file_save.setEnabled(has_active_doc)
        self.act_file_save_as.setEnabled(has_active_doc)

        self.act_wnd_close.setEnabled(has_active_doc)
        self.act_wnd_close_all.setEnabled(has_active_doc)
        self.act_wnd_tile.setEnabled(has_active_doc)
        self.act_wnd_cascade.setEnabled(has_active_doc)
        self.act_wnd_next.setEnabled(has_active_doc)
        self.act_wnd_prev.setEnabled(has_active_doc)

        self.update_menu_edit()

    def update_menu_edit(self) -> None:
        "Create Edit menu with a list of currently opened documents."
        active = self.current_nodeeditor_widget()
        has_active_doc = active is not None
        self.act_paste.setEnabled(has_active_doc)
        self.act_cut.setEnabled(has_active_doc and active.has_selected_items())
        self.act_copy.setEnabled(has_active_doc and active.has_selected_items())
        self.act_delete.setEnabled(has_active_doc and active.has_selected_items())

        self.act_undo.setEnabled(has_active_doc and active.can_undo())
        self.act_redo.setEnabled(has_active_doc and active.can_redo())

    def update_menu_window(self) -> None:
        "Create Window menu with a list of currently opened documents."
        self.menu_window.clear()

        nodes_toolbar = some(self.menu_window.addAction("Nodes Toolbar"))
        nodes_toolbar.triggered.connect(self.on_window_nodes_toolbar)
        nodes_toolbar.setCheckable(True)
        nodes_toolbar.setChecked(self.nodes_dock.isVisible())

        self.menu_window.addSeparator()
        self.menu_window.addAction(self.act_wnd_close)
        self.menu_window.addAction(self.act_wnd_close_all)
        self.menu_window.addSeparator()
        self.menu_window.addAction(self.act_wnd_tile)
        self.menu_window.addAction(self.act_wnd_cascade)
        self.menu_window.addSeparator()
        self.menu_window.addAction(self.act_wnd_next)
        self.menu_window.addAction(self.act_wnd_prev)

        windows = self.mdi_area.subWindowList()
        if len(windows) > 0:
            self.menu_window.addSeparator()
        for i, window in enumerate(windows, start=1):
            child = cast(CalculatorSubWindow, window.widget())
            text = f"{i} {child.get_user_friendly_filename()}"
            if i < 10:
                text = f"&{text}"

            action = some(self.menu_window.addAction(text))
            action.setCheckable(True)
            action.setChecked(child is self.current_nodeeditor_widget())
            action.triggered.connect(partial(self.set_active_subwindow, window=window))

    def on_window_nodes_toolbar(self) -> None:
        self.nodes_dock.setVisible(not self.nodes_dock.isVisible())

    def create_toolbars(self) -> None:
        ...

    def create_nodes_dock(self):
        self.nodes_list_widget = QDMDragListbox()
        self.nodes_dock = QDockWidget("Nodes")
        self.nodes_dock.setWidget(self.nodes_list_widget)
        self.nodes_dock.setFloating(False)

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.nodes_dock)

    def create_statusbar(self) -> None:
        self.statusBar().showMessage("Ready")

    def create_mdi_child(self, child_widget: CalculatorSubWindow | None = None,
                         ) -> QMdiSubWindow:
        "Create a child window and put a new or existing node editor into it."
        nodeeditor = child_widget or CalculatorSubWindow()
        subwnd = some(self.mdi_area.addSubWindow(nodeeditor))
        subwnd.setWindowIcon(self.empty_icon)  # for tiled windows
        # nodeeditor.scene.add_item_selected_listener(self.update_menu_edit)
        # nodeeditor.scene.add_items_deselected_listener(self.update_menu_edit)
        nodeeditor.scene.history.add_history_modified_listener(self.update_menu_edit)
        nodeeditor.add_close_event_listener(self.on_subwindow_close)
        return subwnd

    def on_subwindow_close(self, widget: CalculatorSubWindow, event: QCloseEvent | None,
                           ) -> None:
        "Suggest to save a document on close event."
        # TODO: filename is None in all new documents. Fix this.
        existing = self.find_mdi_child(widget.filename)
        self.mdi_area.setActiveSubWindow(existing)
        if event and self.maybe_save():
            event.accept()
        elif event:
            event.ignore()

    def find_mdi_child(self, filename: Path):
        for window in self.mdi_area.subWindowList():
            nodeeditor = cast(CalculatorSubWindow, window.widget())
            if nodeeditor.filename == filename:
                return window
        return None

    def set_active_subwindow(self, window: QMdiSubWindow | None):
        if window:
            self.mdi_area.setActiveSubWindow(window)
