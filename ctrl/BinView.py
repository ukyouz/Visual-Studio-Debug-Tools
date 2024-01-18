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
from ctrl.qtapp import set_app_title
from helper import qtmodel
from plugins import loadpdb
from view import BinView
from view import resource


class PluginNotLoaded(Exception):
    """plugin not loaded"""


@dataclass
class ParseRecord:
    struct: str
    offset: str
    model: Optional[QtCore.QAbstractItemModel] = field(default=None)


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

        self.app_setting = QtCore.QSettings("app.ini", QtCore.QSettings.Format.IniFormat)

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

    def _loadFile(self, fileio: io.BytesIO):
        set_app_title(self.view, getattr(fileio, "name", "noname"))
        tblmodel = qtmodel.HexTable(self.tableView, fileio)
        self.tableView.setModel(tblmodel)

        treemodel = self.treeView.model()
        if isinstance(treemodel, qtmodel.StructTreeModel):
            treemodel.toggleHexMode(self.btnToggleHex.isChecked())
            fileio.seek(self.parse_offset)
            treemodel.loadStream(io.BytesIO(fileio.read()))

    def _onLineOffsetChanged(self):
        model = self.tableView.model()
        if isinstance(model, qtmodel.HexTable):
            model.shiftOffset(self.parse_offset)

    def _onBtnToggleHexClicked(self):
        model = self.treeView.model()
        if isinstance(model, qtmodel.StructTreeModel):
            checked = self.btnToggleHex.isChecked()
            model.toggleHexMode(checked)

    def _onBtnParseClicked(self):
        structname = self.lineStruct.text()
        pdb = self.plugin(loadpdb.LoadPdb)

        def _cb(res):
            self.btnParse.setEnabled(True)
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

        self.btnParse.setEnabled(False)
        self.exec_async(
            pdb.parse_struct,
            structname,
            addr=self.parse_offset,
            count=self.spinParseCount.value(),
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
            "Size",
            "Count",
            "Address",
        ]
        model = qtmodel.StructTreeModel(data, headers)
        if self.fileio:
            # TODO: global address fileio reader
            self.fileio.seek(self.parse_offset)
            model.loadStream(io.BytesIO(self.fileio.read()))
        self.treeView.setModel(model)
        # expand the first item
        self.treeView.setExpanded(model.index(0, 0), True)
        for c in range(model.columnCount()):
            self.treeView.resizeColumnToContents(c)
        return model


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
    window.view.show()
    sys.exit(app.exec())