import io
import sys
from typing import Type

from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import ClsType
from ctrl.qtapp import Plugin
from ctrl.qtapp import set_app_title
from helper import qtmodel
# for pickle to work
from modules.pdbparser.parser import PDB7
from modules.pdbparser.parser import DbiStream
from modules.pdbparser.parser import OldDirectory
from modules.pdbparser.parser import PdbStream
from modules.pdbparser.parser import Stream
from modules.pdbparser.parser import TpiStream
from plugins import loadpdb
from view import BinView


class PluginNotLoaded(Exception):
    """plugin not loaded"""


class BinViewer(AppCtrl, BinView.Ui_MainWindow):
    def __init__(self, fileio=None):
        super().__init__()
        self.view = QtWidgets.QMainWindow()
        self.setupUi(self.view)
        set_app_title(self.view, "")

        # properties
        self.fileio = fileio
        if fileio:
            self._loadFile(fileio)

        # events
        self.actionOpen_File.triggered.connect(self._onFileOpened)
        self.btnParse.clicked.connect(self._onBtnParseClicked)
        self.lineStruct.returnPressed.connect(self._onBtnParseClicked)
        self.lineOffset.returnPressed.connect(self._onBtnParseClicked)

        self._plugins = {}
        self.loadPlugins([
            loadpdb.LoadPdb(self),
        ])

    def loadPlugins(self, plugins: list[Plugin]):
        for p in plugins:
            self._plugins[p.__class__.__name__] = p
            p.setupMenues(self.menubar)
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
                self.view,
                caption="Open File",
                filter="Any (*.*)"
            )
        if filename:
            with open(filename, "rb") as fs:
                self.fileio = io.BytesIO(fs.read())
                self.fileio.name = filename
                self._loadFile(self.fileio)

    def _loadFile(self, fileio: io.IOBase):
        set_app_title(self.view, getattr(fileio, "name", "noname"))
        model = qtmodel.HexTable(self.tableView, fileio)
        self.tableView.setModel(model)
        if self.treeView.model():
            model: qtmodel.StructTreeModel = self.treeView.model()
            model.loadRaw(self.fileio.getvalue())

    def _onBtnParseClicked(self):
        structname = self.lineStruct.text()
        offset = self.lineOffset.text()
        pdb = self.plugin(loadpdb.LoadPdb)

        def _cb(res):
            self._load_tree(res)

        def _err(*args):
            QtWidgets.QMessageBox.warning(
                self.view,
                "PDB Error!",
                "Please load pdbin first!",
            )

        self.exec_async(
            pdb.parse_struct,
            structname,
            add_dummy_root=True,
            finished_cb=_cb,
            errored_cb=_err,
        )

    def _load_tree(self, data: dict):
        headers = [
            "Levelname",
            "Value",
            "Type",
            "Base",
        ]
        model = qtmodel.StructTreeModel(data, headers)
        if self.fileio:
            model.loadRaw(self.fileio.getvalue())
        self.treeView.setModel(model)


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("--file", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)

    fileio = io.BytesIO()
    if args.file:
        with open(args.file, "rb") as fs:
            fileio = io.BytesIO(fs.read())
    window = BinViewer(fileio)
    window.view.show()
    sys.exit(app.exec())