import io
import sys
from dataclasses import dataclass
from dataclasses import field
from typing import Optional

from PyQt6 import QtCore
from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import HistoryMenu
from ctrl.qtapp import set_app_title
from helper import qtmodel
from plugins import loadpdb
from view import WidgetBinParser


@dataclass
class ParseRecord:
    struct: str
    offset: str
    model: Optional[QtCore.QAbstractItemModel] = field(default=None)


class ParseHistoryMenu(HistoryMenu):
    def stringify(self, data: ParseRecord) -> str:
        if data.offset:
            return "%s; %s" % (data.struct, data.offset)
        else:
            return data.struct


class BinParser(QtWidgets.QWidget):
    def __init__(self, app: AppCtrl, fileio=None):
        super().__init__(app)
        self.ui = WidgetBinParser.Ui_Form()
        self.ui.setupUi(self)
        self.app = app
        set_app_title(self, "")

        # properties
        self.parse_hist = ParseHistoryMenu(self.ui.btnHistory)
        self.parse_hist.actionTriggered.connect(self._onParseHistoryClicked)
        self.fileio = fileio
        if fileio:
            self._loadFile(fileio)

        # events
        self.ui.btnParse.clicked.connect(self._onBtnParseClicked)
        self.ui.lineStruct.returnPressed.connect(self._onBtnParseClicked)
        self.ui.lineOffset.returnPressed.connect(self._onBtnParseClicked)
        self.ui.lineOffset.editingFinished.connect(self._onLineOffsetChanged)
        self.ui.btnToggleHex.clicked.connect(self._onBtnToggleHexClicked)
        self.ui.treeView.expanded.connect(lambda: self.ui.treeView.resizeColumnToContents(0))

    @property
    def parse_offset(self):
        try:
            return eval(self.ui.lineOffset.text())
        except:
            return 0

    def _onFileOpened(self, filename=False):
        if not filename:
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                caption="Open File",
                filter="Any (*.*)"
            )
        if filename:
            with open(filename, "rb") as fs:
                self.fileio = io.BytesIO(fs.read())
                self.fileio.name = filename
                self._loadFile(self.fileio)

    def _loadFile(self, fileio: io.BytesIO):
        set_app_title(self, getattr(fileio, "name", "noname"))
        tblmodel = qtmodel.HexTable(fileio, self.ui.tableView)
        self.ui.tableView.setModel(tblmodel)

        treemodel = self.ui.treeView.model()
        if isinstance(treemodel, qtmodel.StructTreeModel):
            treemodel.toggleHexMode(self.ui.btnToggleHex.isChecked())
            fileio.seek(self.parse_offset)
            treemodel.loadStream(io.BytesIO(fileio.read()))

    def _onLineOffsetChanged(self):
        model = self.ui.tableView.model()
        if isinstance(model, qtmodel.HexTable):
            model.shiftOffset(self.parse_offset)

    def _onBtnToggleHexClicked(self):
        model = self.ui.treeView.model()
        if isinstance(model, qtmodel.StructTreeModel):
            checked = self.ui.btnToggleHex.isChecked()
            model.toggleHexMode(checked)

    def _onBtnParseClicked(self):
        structname = self.ui.lineStruct.text()
        pdb = self.app.plugin(loadpdb.LoadPdb)

        def _cb(res):
            self.ui.btnParse.setEnabled(True)
            if res is None:
                return
            model = self._load_tree(res)
            if model.rowCount():
                p = ParseRecord(structname, self.ui.lineOffset.text(), model)
                self.parse_hist.add_data(p)

        def _err(*args):
            QtWidgets.QMessageBox.warning(
                self,
                "PDB Error!",
                "Please load pdbin first!",
            )

        self.ui.btnParse.setEnabled(False)
        self.app.exec_async(
            pdb.parse_struct,
            structname,
            addr=self.parse_offset,
            count=self.ui.spinParseCount.value(),
            add_dummy_root=True,
            finished_cb=_cb,
            errored_cb=_err,
        )

    def _onParseHistoryClicked(self, data: ParseRecord):
        self.ui.lineStruct.setText(data.struct)
        self.ui.lineOffset.setText(data.offset)
        self._onLineOffsetChanged()
        if data.model:
            self.ui.treeView.setModel(data.model)

    def _load_tree(self, data: dict):
        model = qtmodel.StructTreeModel(data)
        if self.fileio:
            # TODO: global address fileio reader
            self.fileio.seek(self.parse_offset)
            model.loadStream(io.BytesIO(self.fileio.read()))
        self.ui.treeView.setModel(model)
        # expand the first item
        self.ui.treeView.setExpanded(model.index(0, 0), True)
        for c in range(model.columnCount()):
            self.ui.treeView.resizeColumnToContents(c)
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
    window = BinParser(None, fileio)
    window.show()
    sys.exit(app.exec())