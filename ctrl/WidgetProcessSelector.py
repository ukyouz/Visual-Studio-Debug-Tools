import io
import os
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
from ctrl.qtapp import MenuAction
from ctrl.qtapp import Plugin
from ctrl.qtapp import PluginNotLoaded
from ctrl.qtapp import set_app_title
from helper import qtmodel
from modules.winkernel import ProcessDebugger
from plugins import debugger
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

        # ui events
        self.ui.btnAttach.clicked.connect(self.attach_current_selected_process)

        self.load_ui()

        self.app.loadPlugins([
            debugger.Debugger(self.app),
        ])

    def load_ui(self):
        def _cb_load_processes(unique_processes):
            if not unique_processes:
                return
            if len(unique_processes):
                self.ui.comboProcess.addItems(unique_processes)
                self.ui.comboProcess.setCurrentIndex(0)

            if val := self.app.app_setting.value("Process/filename", ""):
                if val in unique_processes:
                    self.ui.comboProcess.setCurrentText(val)

        self.ui.frameDebugger.setEnabled(False)
        self.app.exec_async(
            self._get_processes,
            finished_cb=_cb_load_processes,
        )

    def _get_processes(self):
        processes = ProcessDebugger.list_processes()
        pnames = [x.get_filename() for x in processes]
        pnames = [os.path.basename(x) for x in pnames if x]
        pcounter = Counter(pnames)
        unique_processes = [x for x in pnames if pcounter[x] == 1]
        return sorted(unique_processes)

    def attach_current_selected_process(self, callback=None):
        pname = self.ui.comboProcess.currentText()
        dbg = self.app.plugin(debugger.Debugger)
        def _cb():
            self.ui.frameDebugger.setEnabled(True)
            self.app.app_setting.setValue("Process/filename", pname)
            if callback:
                callback()

        self.app.exec_async(
            dbg.attach_process,
            name=pname,
            finished_cb=_cb,
        )


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    window = ProcessSelector(None)
    window.show()
    sys.exit(app.exec())