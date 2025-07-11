import io
import logging
import os
import sys
from dataclasses import dataclass
from dataclasses import field
from functools import partial
from pathlib import Path
from typing import Optional
from typing import Type

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import ClsType
from ctrl.qtapp import Plugin
from ctrl.qtapp import PluginNotLoaded
from ctrl.qtapp import set_app_title
from ctrl.WidgetBinParser import BinParser
from helper import qtmodel
from plugins import help_menu
from plugins import loadpdb
from plugins import run_script
from plugins import translator
from view import BinView
from view import resource

logger = logging.getLogger(__name__)


@dataclass
class ParseRecord:
    struct: str
    offset: str
    model: Optional[QtCore.QAbstractItemModel] = field(default=None)


class BinViewer(AppCtrl):
    def __init__(self, filenames: list[str] = None):
        super().__init__()
        self.ui = BinView.Ui_MainWindow()
        self.ui.setupUi(self)
        set_app_title(self, "")
        self.app_dir = Path(__file__).parent
        self.setWindowIcon(QtGui.QIcon(str(self.app_dir / "view/images/dsquery_153.ico")))

        # events
        self.ui.actionOpen_File.triggered.connect(self._onFileOpened)
        self.ui.actionHide_Binary_View.triggered.connect(self._focusActiveWidget)
        self.ui.btnOpenFiles.clicked.connect(self._onFileOpened)
        self.ui.treeExplorer.setModel(qtmodel.FileExplorerModel(Path()))
        self.ui.treeExplorer.doubleClicked.connect(self._onExplorerDoubleClicked)

        self._plugins = {}
        self.subwidgets = {}
        self.loadPlugins([
            run_script.RunScript(self),
            loadpdb.LoadPdb(self),
            translator.Translator(self),
            help_menu.AboutMe(self),
        ])

        self.cmd.register("ExportParsingResultAsCsvFile", self._export_active_window)
        self.setupMenues(self.menu("Tool"), [
            {
                "name": "Export parsing result as csv...",
                "command": "ExportParsingResultAsCsvFile",
                "position": 0,
            },
        ])

        if filenames:
            self._onFileOpened(filenames)

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

    def _onFileOpened(self, filenames: list[str] | bool =False):
        if not filenames:
            filenames, _ = QtWidgets.QFileDialog.getOpenFileNames(
                self,
                caption="Open Files",
                filter="Any (*.*)"
            )
        for f in filenames:
            if not os.path.isfile(f):
                continue
            model = self.ui.treeExplorer.model()
            if isinstance(model, qtmodel.FileExplorerModel):
                indexes = model.addFiles([f])
                self.ui.treeExplorer.scrollTo(indexes[0], QtWidgets.QAbstractItemView.ScrollHint.EnsureVisible)
                self.ui.treeExplorer.setCurrentIndex(indexes[0])
                QtCore.QTimer.singleShot(0, partial(self._loadFile, f))

    def _loadFile(self, f: str):
        with open(f, "rb") as fs:
            fileio = io.BytesIO(fs.read())
            fileio.name = f
            widget = BinParser(self)
            window = self.ui.mdiArea.addSubWindow(widget)
            widget.loadFile(fileio)
            widget.show()
            fpath = Path(getattr(fileio, "name", ""))
            logger.info("File loaded: %s" % fpath)
            try:
                self.subwidgets[fpath] = window
            except KeyError:
                logger.warning("Document not ready to open: %s" % fpath)

    def _onExplorerDoubleClicked(self, index):
        model = self.ui.treeExplorer.model()
        if not isinstance(model, qtmodel.FileExplorerModel):
            return
        fpath = model.pathFromIndex(index)
        window = self.subwidgets[fpath]
        self.ui.mdiArea.setActiveSubWindow(window)

    def _export_active_window(self):
        win = self.ui.mdiArea.activeSubWindow()
        widget = win.widget()
        if getattr(widget, "export_as_csv", None):
            widget.export_as_csv()
        else:
            logger.warning("No implantation of 'export_as_csv' method for %r" % widget)

    def _focusActiveWidget(self):
        win = self.ui.mdiArea.activeSubWindow()
        widget = win.widget()
        if getattr(widget, "focusParseResult", None):
            widget.focusParseResult()
        else:
            logger.warning("No implantation of 'focusParseResult' method for %r" % widget)


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("files", nargs="*", default=[])
    args = p.parse_args()

    # https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7
    import ctypes
    myappid = __file__
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QtWidgets.QApplication(sys.argv)
    window = BinViewer(args.files)
    window.show()
    sys.exit(app.exec())