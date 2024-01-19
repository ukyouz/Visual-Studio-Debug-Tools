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
from ctrl.qtapp import PluginNotLoaded
from ctrl.qtapp import set_app_title
from helper import qtmodel
from plugins import debugger
from view import WidgetMemory
from view import resource


class Memory(QtWidgets.QWidget):
    def __init__(self, app: AppCtrl):
        super().__init__(app)
        self.ui = WidgetMemory.Ui_Form()
        self.ui.setupUi(self)
        set_app_title(self, "")

        self.app = app

        self.ui.lineAddress.returnPressed.connect(self._loadMemory)
        self.ui.lineSize.returnPressed.connect(self._loadMemory)

    @property
    def requestAddress(self):
        try:
            return eval(self.ui.lineAddress.text())
        except:
            return 0

    @property
    def requestSize(self):
        try:
            return eval(self.ui.lineSize.text())
        except:
            return 1024

    def _loadMemory(self):
        dbg = self.app.plugin(debugger.Debugger)
        if dbg is None:
            raise PluginNotLoaded()
        mem = dbg.get_memory_stream()

        model = qtmodel.HexTable(mem)
        model.viewOffset = self.requestAddress
        model.viewMaxLength = self.requestSize
        self.ui.tableView.setModel(model)
        self.ui.tableView.resizeColumnsToContents()


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    window = Memory(None)
    window.show()
    sys.exit(app.exec())