import argparse
import logging
import sys

from qtpy.QtWidgets import QApplication

from qt_node_editor.node_editor_wnd import NodeEditorWnd

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    LOG_LEVEL = "DEBUG" if args.debug else "INFO"
    FORMAT = "[%(filename)s:%(lineno)s %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, level=LOG_LEVEL)

    app = QApplication(sys.argv)
    wnd = NodeEditorWnd()
    sys.exit(app.exec())
