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
from view import WidgetMemory
from view import resource


class PluginNotLoaded(Exception):
    """plugin not loaded"""


class CtrlMemory(WidgetMemory.Ui_Form):
    def __init__(self, ctrl):
        super().__init__()
        self.view = QtWidgets.QWidget(ctrl.view)
        self.setupUi(self.view)
        set_app_title(self.view, "")

        self.ctrl = ctrl


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    window = CtrlMemory(None)
    window.view.show()
    sys.exit(app.exec())