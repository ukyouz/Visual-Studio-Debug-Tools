import io
import sys
from collections import Counter
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
from modules.winkernel import ProcessDebugger
from plugins import loadpdb
from view import WidgetProcessSelector
from view import resource


class ProcessSelector(QtWidgets.QWidget):
    def __init__(self, app: AppCtrl):
        super().__init__()
        self.ui = WidgetProcessSelector.Ui_Form()
        self.ui.setupUi(self)
        set_app_title(self, "")

        self.app = app

        self.load_ui()

    def load_ui(self):
        def _cb_load_processes(unique_processes):
            if not unique_processes:
                return
            if len(unique_processes):
                self.ui.comboProcess.addItems(unique_processes)
                self.ui.comboProcess.setCurrentIndex(0)
        self.app.exec_async(
            self._get_processes,
            finished_cb=_cb_load_processes,
        )

    def _get_processes(self):
        processes = ProcessDebugger.list_processes()
        pnames = [x.get_filename() for x in processes]
        pcounter = Counter(pnames)
        unique_processes = [x for x in pnames if pcounter[x] == 1 and x]
        return sorted(unique_processes)


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    window = ProcessSelector(None)
    window.show()
    sys.exit(app.exec())