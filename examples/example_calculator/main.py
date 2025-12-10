import argparse
import configparser
import logging
import os
import sys

from calc_window import CalculatorWindow
from qtpy.QtWidgets import QApplication

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    LOG_LEVEL = "DEBUG" if args.debug else "INFO"
    # Force debug loggging level when run in VS Code debug mode
    if "PYDEVD_USE_FRAME_EVAL" in os.environ:
        LOG_LEVEL = "DEBUG"
    FORMAT = "[%(filename)s:%(lineno)s %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, level=LOG_LEVEL)

    config = configparser.ConfigParser()
    if config.read('conf/logging_config.toml'):
        for logger_name, level in config["levels"].items():
            logging.getLogger(logger_name).setLevel(level.upper())

    app = QApplication(sys.argv)
    wnd = CalculatorWindow()
    wnd.show()
    sys.exit(app.exec())
