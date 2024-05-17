import io
import os
import sys
from dataclasses import dataclass
from dataclasses import field
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


@dataclass
class ParseRecord:
    struct: str
    offset: str
    model: Optional[QtCore.QAbstractItemModel] = field(default=None)


class BinViewer(AppCtrl):
    def __init__(self, filenames=None):
        super().__init__()
        self.ui = BinView.Ui_MainWindow()
        self.ui.setupUi(self)
        set_app_title(self, "")
        self.app_dir = Path(__file__).parent
        self.setWindowIcon(QtGui.QIcon(str(self.app_dir / "view/images/dsquery_153.ico")))

        # events
        self.ui.actionOpen_File.triggered.connect(self._onFileOpened)
        self.ui.btnOpenFiles.clicked.connect(self._onFileOpened)
        self.ui.treeExplorer.setModel(qtmodel.FileExplorerModel(Path()))

        self._plugins = {}
        self.subwidgets = []
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
            for f in filenames:
                if os.path.isfile(f):
                    self._onFileOpened(f)

    def loadPlugins(self, plugins: list[Plugin]):
        for p in plugins:
            self._plugins[p.__class__.__name__] = p
            self.setupMenues(self.ui.menubar, p.registerMenues())
            for cmdname, fn in p.registerCommands():
                self.cmd.register(cmdname, fn)
            p.post_init()

    def plugin(self, plg_cls: Type[ClsType]) -> ClsType:
        try:
            return self._plugins[plg_cls.__name__]
        except KeyError:
            raise PluginNotLoaded(plg_cls)

    def _onFileOpened(self, filename=""):
        if not filename:
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                caption="Open File",
                filter="Any (*.*)"
            )
        if filename:
            model = self.ui.treeExplorer.model()
            if isinstance(model, qtmodel.FileExplorerModel):
                indexes = model.addFiles([filename])
                self.ui.treeExplorer.scrollTo(indexes[0], QtWidgets.QAbstractItemView.ScrollHint.EnsureVisible)
                self.ui.treeExplorer.setCurrentIndex(indexes[0])

            with open(filename, "rb") as fs:
                fileio = io.BytesIO(fs.read())
                fileio.name = filename
                QtCore.QTimer.singleShot(0, lambda: self._loadFile(fileio))

    def _loadFile(self, fileio: io.BytesIO):
        widget = BinParser(self)
        window = self.ui.mdiArea.addSubWindow(widget)
        widget.loadFile(fileio)
        widget.show()
        self.subwidgets.append(window)

    def _export_active_window(self):
        win = self.ui.mdiArea.activeSubWindow()
        widget = win.widget()
        if getattr(widget, "export_as_csv"):
            widget.export_as_csv()


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("files", nargs="*", default="")
    args = p.parse_args()

    # https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7
    import ctypes
    myappid = __file__
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QtWidgets.QApplication(sys.argv)
    window = BinViewer(args.files)
    window.show()
    sys.exit(app.exec())