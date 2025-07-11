import logging
import sys
from functools import partial
from datetime import datetime
from pathlib import Path
from typing import Type

from PyQt6 import QtGui
from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import ClsType
from ctrl.qtapp import Plugin
from ctrl.qtapp import PluginNotLoaded
from ctrl.qtapp import set_app_title
from ctrl.WidgetProcessSelector import ProcessSelector
from plugins import debugger
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

        editToolBar = QtWidgets.QToolBar("Process", self)
        editToolBar.setMovable(False)
        processSelector = ProcessSelector(self)
        self.addToolBar(editToolBar)
        editToolBar.addWidget(processSelector)

        def _re_attach(callback=None):
            processSelector.detach_current_selected_process(
                callback=partial(self.run_cmd, "AttachCurrentProcess", callback=callback),
            )
        self.cmd.register("AttachCurrentProcess", processSelector.attach_current_selected_process)
        self.cmd.register("ReloadCurrentProcess", _re_attach)

        d = self.plugin(dock.Dock)
        dbg = self.plugin(debugger.ExeDebugger)
        d.load_plugins(dbg)
        d.init_views()

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