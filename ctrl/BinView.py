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
from ctrl.WidgetBinParser import BinParser
from helper import qtmodel
from plugins import loadpdb
from view import BinView
from view import resource


@dataclass
class ParseRecord:
    struct: str
    offset: str
    model: Optional[QtCore.QAbstractItemModel] = field(default=None)


class BinViewer(AppCtrl):
    def __init__(self, fileio=None):
        super().__init__()
        self.ui = BinView.Ui_MainWindow()
        self.ui.setupUi(self)
        set_app_title(self, "")

        # properties
        if fileio:
            self._loadFile(fileio)

        # events
        self.ui.actionOpen_File.triggered.connect(self._onFileOpened)

        self._plugins = {}
        self.subwidgets = []
        self.loadPlugins([
            loadpdb.LoadPdb(self),
        ])


    def loadPlugins(self, plugins: list[Plugin]):
        for p in plugins:
            self._plugins[p.__class__.__name__] = p
            p.setupMenues(self.ui.menubar)
            for cmdname, fn in p.registerCommands():
                self.cmd.register(cmdname, fn)

    def plugin(self, plg_cls: Type[ClsType]) -> ClsType:
        try:
            return self._plugins[plg_cls.__name__]
        except KeyError:
            raise PluginNotLoaded(plg_cls)

    def _onFileOpened(self, filename=False):
        if not filename:
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                caption="Open File",
                filter="Any (*.*)"
            )
        if filename:
            with open(filename, "rb") as fs:
                fileio = io.BytesIO(fs.read())
                fileio.name = filename
                self._loadFile(fileio)

    def _loadFile(self, fileio: io.BytesIO):
        widget = BinParser(self, fileio)
        window = self.ui.mdiArea.addSubWindow(widget)
        widget.show()
        self.subwidgets.append(window)


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)

    fileio = io.BytesIO()
    if args.file:
        with open(args.file, "rb") as fs:
            fileio = io.BytesIO(fs.read())
    window = BinViewer(fileio)
    window.show()
    sys.exit(app.exec())