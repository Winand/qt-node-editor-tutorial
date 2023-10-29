import sys

from qtpy.QtWidgets import QApplication

from qt_node_editor.node_editor_wnd import NodeEditorWnd

if __name__ == '__main__':
    app = QApplication(sys.argv)
    wnd = NodeEditorWnd()
    sys.exit(app.exec())
