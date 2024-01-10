import io
import sys
from dataclasses import dataclass
from dataclasses import field
from typing import Type

from PyQt6 import QtCore
from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import ClsType
from ctrl.qtapp import HistoryMenu
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


@dataclass
class ParseRecord:
    struct: str
    offset: str
    model: QtCore.QAbstractItemModel = field(default=None)


class ParseHistoryMenu(HistoryMenu):
    def stringify(self, data: ParseRecord) -> str:
        return "%s; %s" % (data.struct, data.offset)


class BinViewer(AppCtrl, BinView.Ui_MainWindow):
    def __init__(self, fileio=None):
        super().__init__()
        self.view = QtWidgets.QMainWindow()
        self.setupUi(self.view)
        set_app_title(self.view, "")

        # properties
        self.parse_hist = ParseHistoryMenu(self.btnHistory)
        self.parse_hist.actionTriggered.connect(self._onParseHistoryClicked)
        self.fileio = fileio
        if fileio:
            self._loadFile(fileio)

        # events
        self.actionOpen_File.triggered.connect(self._onFileOpened)
        self.btnParse.clicked.connect(self._onBtnParseClicked)
        self.lineStruct.returnPressed.connect(self._onBtnParseClicked)
        self.lineOffset.returnPressed.connect(self._onBtnParseClicked)
        self.lineOffset.editingFinished.connect(self._onLineOffsetChanged)
        self.btnToggleHex.clicked.connect(self._onBtnToggleHexClicked)

        self._plugins = {}
        self.loadPlugins([
            loadpdb.LoadPdb(self),
        ])

    @property
    def parse_offset(self):
        try:
            return eval(self.lineOffset.text())
        except:
            return 0

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
        tblmodel = qtmodel.HexTable(self.tableView, fileio)
        self.tableView.setModel(tblmodel)
        if self.treeView.model() and self.fileio:
            treemodel: qtmodel.StructTreeModel = self.treeView.model()
            treemodel.toggleHexMode(self.btnToggleHex.isChecked())
            treemodel.loadRaw(self.fileio.getvalue())

    def _onLineOffsetChanged(self):
        model: qtmodel.HexTable = self.tableView.model()
        if model:
            model.shiftOffset(self.parse_offset)

    def _onBtnToggleHexClicked(self):
        model: qtmodel.StructTreeModel = self.treeView.model()
        if model:
            checked = self.btnToggleHex.isChecked()
            model.toggleHexMode(checked)

    def _onBtnParseClicked(self):
        structname = self.lineStruct.text()
        pdb = self.plugin(loadpdb.LoadPdb)

        def _cb(res):
            model = self._load_tree(res)
            if model.rowCount():
                p = ParseRecord(structname, self.lineOffset.text(), model)
                self.parse_hist.add_data(p)

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

    def _onParseHistoryClicked(self, data: ParseRecord):
        self.lineStruct.setText(data.struct)
        self.lineOffset.setText(data.offset)
        self._onLineOffsetChanged()
        if data.model:
            self.treeView.setModel(data.model)

    def _load_tree(self, data: dict):
        headers = [
            "Levelname",
            "Value",
            "Type",
            "Base",
            "Size",
            "Address",
        ]
        model = qtmodel.StructTreeModel(data, headers)
        if self.fileio:
            model.setAddress(self.parse_offset)
            model.loadRaw(self.fileio.getvalue()[self.parse_offset:])
        self.treeView.setModel(model)
        # expand the first item
        self.treeView.setExpanded(model.index(0, 0), True)
        return model


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