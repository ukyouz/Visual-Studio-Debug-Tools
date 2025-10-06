import logging
import sys
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Type

from PyQt6 import QtGui
from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import ClsType
from ctrl.qtapp import Plugin
from ctrl.qtapp import PluginNotLoaded
from ctrl.qtapp import set_app_title
from ctrl.WidgetFileSelector import FileSelector
from ctrl.WidgetProcessSelector import ProcessSelector
from plugins import dock
from plugins import help_menu
from plugins import loadpdb
from plugins import run_script
from plugins import translator
from view import VSdebugger
from view import resource

logger = logging.getLogger(__name__)

_log_file = Path(__file__).parent / "log/VSdebugger.txt"
_log_file.parent.mkdir(parents=True, exist_ok=True)
_handler = logging.FileHandler(_log_file)
_fmt = logging.Formatter(
    "[%(asctime)s][%(name)-5s][%(levelname)-5s] %(message)s (%(filename)s:%(lineno)d)",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_handler.setFormatter(_fmt)
logging.getLogger().addHandler(_handler)


class VisualStudioDebugger(AppCtrl):
    def __init__(self):
        super().__init__()
        self.ui = VSdebugger.Ui_MainWindow()
        self.ui.setupUi(self)
        set_app_title(self, "")
        self.app_dir = Path(__file__).parent
        self.setWindowIcon(QtGui.QIcon(str(self.app_dir / "view/images/vsjitdebugger_VSJITDEBUGGER.ICO.ico")))

        self.ui.checkLogWrap.stateChanged.connect(lambda on: self.ui.plainTextLog.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.WidgetWidth if on else QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap))
        self.ui.btnClearLog.clicked.connect(lambda: self.ui.plainTextLog.clear())

        # load the translator first to apply language setting
        t = translator.Translator(self)
        t.post_init()

        self._plugins = {}
        self.loadPlugins([
            run_script.RunScript(self),
            loadpdb.LoadPdb(self),
            dock.Dock(self),
            t,
            help_menu.AboutMe(self),
        ])

        self.setupMenues(
            self.ui.menubar,
            [
                {
                    "name": self.tr("Source"),
                    "actionGroup": True,
                    "position": 1,
                    "submenus": [
                        {
                            "name": "Runtime EXE",
                            "command": "SetSourceToRuntimeExe",
                            "checked": True,
                        },
                        {
                            "name": "Minidump File",
                            "command": "SetSourceToMinidumpFile",
                        },
                    ],
                },
            ]
        )
        self.editToolBar = QtWidgets.QToolBar("toolbarEdit", self)
        self.editToolBar.setMovable(False)
        self.toolbarActions = {
            ProcessSelector.__name__: ProcessSelector(self),
            FileSelector.__name__: FileSelector(self),
        }
        self.addToolBar(self.editToolBar)
        self.cmd.register("SetSourceToRuntimeExe", partial(self._set_source_to, ProcessSelector))
        self.cmd.register("SetSourceToMinidumpFile", partial(self._set_source_to, FileSelector))
        self.run_cmd("SetSourceToRuntimeExe")

        d = self.plugin(dock.Dock)
        d.init_views()

    def _set_source_to(self, target_cls):
        for name, w in self.toolbarActions.items():
            action = self.editToolBar.addWidget(w)
            action.setVisible(target_cls.__name__ == name)

    def loadPlugins(self, plugins: list[Plugin]):
        for p in plugins:
            self._plugins[p.__class__.__name__] = p
            self.setupMenues(self.ui.menubar, p.registerMenues())
            for cmdname, fn in p.registerCommands():
                self.cmd.register(cmdname, fn)
            p.post_init()

    def plugin(self, plugin_cls: Type[ClsType]) -> ClsType:
        try:
            return self._plugins[plugin_cls.__name__]
        except KeyError:
            raise PluginNotLoaded(plugin_cls)

    def log(self, msg):
        self.ui.tabWidget.setCurrentIndex(0)
        now = datetime.now()
        timestamp = now.isoformat(sep=" ", timespec="milliseconds")
        self.ui.plainTextLog.appendPlainText(f"[{timestamp}] {msg}")


if __name__ == '__main__':
    # https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7
    import ctypes
    myappid = __file__
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QtWidgets.QApplication(sys.argv)
    window = VisualStudioDebugger()

    window.show()
    sys.exit(app.exec())