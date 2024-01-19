import io
import sys
from dataclasses import dataclass
from dataclasses import field
from typing import Optional
from typing import Type

from PyQt6 import QtCore
from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import ClsType
from ctrl.qtapp import HistoryMenu
from ctrl.qtapp import Plugin
from ctrl.qtapp import set_app_title
from helper import qtmodel
from plugins import loadpdb
from view import WidgetDockTitleBar
from view import resource


class DockTitleBar(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QDockWidget):
        super().__init__(parent)
        self.ui = WidgetDockTitleBar.Ui_Form()
        self.ui.setupUi(self)
        self.ui.btnMore.setContentsMargins(0, 0, 0, 0)
        set_app_title(self, "")

        parent.installEventFilter(self)

    def eventFilter(self, obj: QtCore.QObject, e: QtCore.QEvent) -> bool:
        # ref: https://github.com/yjg30737/pyqt-custom-titlebar-window/blob/main/pyqt_custom_titlebar_window/customTitlebarWindow.py
        if isinstance(obj, QtWidgets.QDockWidget):
            if e.type() == QtCore.QEvent.Type.WindowTitleChange:
                self.ui.labelTitle.setText(obj.windowTitle())
        return False



if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    window = DockTitleBar(None)
    window.show()
    sys.exit(app.exec())