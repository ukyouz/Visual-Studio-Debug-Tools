import os
import sys
from collections import Counter

from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import i18n
from ctrl.qtapp import set_app_title
from modules.winkernel import ProcessDebugger
from plugins import debugger
from view import WidgetProcessSelector

tr = lambda txt: i18n("Memory", txt)


class ProcessSelector(QtWidgets.QWidget):
    def __init__(self, app: AppCtrl):
        super().__init__()
        self.ui = WidgetProcessSelector.Ui_Form()
        self.ui.setupUi(self)
        set_app_title(self, "")

        self.app = app

        # ui events
        self.ui.btnAttach.clicked.connect(self.attach_current_selected_process)
        self.ui.btnDetach.clicked.connect(self.detach_current_selected_process)
        self.ui.frameDebugger.setVisible(False)

        self.app.loadPlugins([
            debugger.Debugger(self.app),
        ])

        self.app.cmd.register("RefreshProcesses", self.load_ui)
        self.app.setupMenues(self.app.menu("Tool"), [
            {
                "name": "Refresh processes",
                "command": "RefreshProcesses",
                "icon": ":icon/images/ctrl/VirtualMachineRefresh_16x.svg",
                "shortcut": "F5",
                "position": 0,
            },
            { "name": "---", },
        ])

        self.load_ui(False)

    def load_ui(self, show_status=True):
        def _cb_load_processes(unique_processes):
            if not unique_processes:
                return
            self.ui.comboProcess.clear()
            if len(unique_processes):
                self.ui.comboProcess.addItems(unique_processes)
                self.ui.comboProcess.setCurrentIndex(0)

            if val := self.app.app_setting.value("Process/filename", ""):
                if val in unique_processes:
                    self.ui.comboProcess.setCurrentText(val)
            if show_status:
                self.app.statusBar().showMessage(tr("Processes are reloaded."))

        self.update_ui_states(False)
        self.app.exec_async(
            self._get_processes,
            finished_cb=_cb_load_processes,
        )
        if show_status:
            self.app.statusBar().showMessage(tr("Refreshing processes..."))

    def update_ui_states(self, process_attached: bool):
        self.ui.comboProcess.setEnabled(not process_attached)
        self.ui.frameDebugger.setEnabled(process_attached)
        self.ui.btnAttach.setVisible(not process_attached)
        self.ui.btnDetach.setVisible(process_attached)
        self.app.action("Refresh processes").setEnabled(not process_attached)

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
        def _cb(error):
            process_attached = error is None
            if not process_attached:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.__class__.__name__,
                    str(error),
                )
            else:
                self.app.app_setting.setValue("Process/filename", pname)
                if callback:
                    callback()
            self.update_ui_states(process_attached)

        self.app.exec_async(
            dbg.attach_process,
            name=pname,
            finished_cb=_cb,
        )

    def detach_current_selected_process(self):
        dbg = self.app.plugin(debugger.Debugger)

        self.app.exec_async(
            dbg.detach_process,
            finished_cb=lambda: self.update_ui_states(False),
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