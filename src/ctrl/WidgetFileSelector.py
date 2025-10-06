import sys
from functools import partial
from pathlib import Path

from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import set_app_title
from plugins import debugger
from plugins import dock
from view import WidgetFileSelector


class FileSelector(QtWidgets.QWidget):
    def __init__(self, app: AppCtrl):
        super().__init__()
        self.ui = WidgetFileSelector.Ui_Form()
        self.ui.setupUi(self)
        set_app_title(self, "")

        self.app = app

        # ui events
        self.ui.btnOpen.clicked.connect(self.select_minidump_file)
        self.ui.btnContinue.clicked.connect(self.load_minidump_file)
        self.ui.btnStop.clicked.connect(partial(self.update_ui_states, False))
        self.update_ui_states(False)

        self.app.loadPlugins([
            debugger.MiniDumpDebugger(self.app),
        ])

        self.app.cmd.register("OpenMinidumpFile", self.select_minidump_file)

        if val := self.app.app_setting.value("Minidump/filename", ""):
            if Path(val).exists():
                self.select_minidump_file(val)

    def select_minidump_file(self, filename=""):
        if not filename:
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                caption="Open Minidump File",
                filter="Dump File (*.dmp)",
            )
        if filename:
            self.ui.labelFilename.setText(filename)

    def load_minidump_file(self, filename=""):
        if not filename:
            filename = self.ui.labelFilename.text()
        self.app.app_setting.setValue("Minidump/filename", filename)
        dbg = self.app.plugin(debugger.MiniDumpDebugger)
        d = self.app.plugin(dock.Dock)
        d.load_debugger(dbg)
        self.update_ui_states(True)
        self.app.exec_async(partial(dbg.load_file, filename))

    def update_ui_states(self, process_attached: bool):
        self.ui.btnOpen.setEnabled(not process_attached)
        self.ui.btnStop.setEnabled(process_attached)
        self.ui.btnContinue.setVisible(not process_attached)
        self.ui.btnStop.setVisible(process_attached)


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    window = FileSelector(None)
    window.show()
    sys.exit(app.exec())