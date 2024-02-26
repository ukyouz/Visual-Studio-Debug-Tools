import io
import sys
from dataclasses import dataclass
from dataclasses import field
from typing import Literal
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
    count: int
    parse_mode: Literal["tree", "table"]
    model: Optional[QtCore.QAbstractItemModel] = field(default=None)


class ParseHistoryMenu(HistoryMenu):
    def stringify(self, data: ParseRecord) -> str:
        num = "[%d]" % data.count if data.count > 1 else ""
        struct = "(%s *)" % data.struct if data.parse_mode == "table" else data.struct
        if data.offset:
            return "%s%s; %s" % (struct, num, data.offset)
        else:
            return "%s%s" % (struct, num)


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
        self.ui.checkParseTable.clicked.connect(self._onCheckParseTableClicked)
        self.ui.lineStruct.returnPressed.connect(self._onBtnParseClicked)
        self.ui.lineOffset.returnPressed.connect(self._onBtnParseClicked)
        self.ui.lineOffset.editingFinished.connect(self._onLineOffsetChanged)
        self.ui.btnToggleHex.clicked.connect(self._onBtnToggleHexClicked)
        self.ui.btnToggleChar.clicked.connect(self._onBtnToggleCharClicked)
        self.ui.treeView.expanded.connect(lambda: self.ui.treeView.resizeColumnToContents(0))
        self.ui.treeView.setItemDelegate(qtmodel.BorderItemDelegate())
        self.ui.tableMemory.setItemDelegate(qtmodel.BorderItemDelegate())

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
        tblmodel = qtmodel.HexTable(fileio, self.ui.tableMemory)
        self.ui.tableMemory.setModel(tblmodel)

    def _onLineOffsetChanged(self):
        model = self.ui.tableMemory.model()
        if isinstance(model, qtmodel.HexTable):
            model.shiftOffset(self.parse_offset)

    def _onBtnToggleHexClicked(self):
        page = self.ui.stackedWidget.currentWidget()
        if page is self.ui.pageTable:
            model = self.ui.tableView.model()
            if isinstance(model, qtmodel.StructTableModel):
                model.toggleHexMode(self.ui.btnToggleHex.isChecked())
        else:
            model = self.ui.treeView.model()
            if isinstance(model, qtmodel.StructTreeModel):
                model.toggleHexMode(self.ui.btnToggleHex.isChecked())

    def _onBtnToggleCharClicked(self):
        page = self.ui.stackedWidget.currentWidget()
        if page is self.ui.pageTable:
            model = self.ui.tableView.model()
            if isinstance(model, qtmodel.StructTableModel):
                model.toggleCharMode(self.ui.btnToggleChar.isChecked())

    def _onCheckParseTableClicked(self):
        is_array = self.ui.checkParseTable.isChecked()
        old_count = self.ui.spinParseCount.value()
        if is_array:
            if old_count == 1:
                self.ui.spinParseCount.setValue(0)
        else:
            if old_count == 0:
                self.ui.spinParseCount.setValue(1)

    def _onBtnParseClicked(self):
        structname = self.ui.lineStruct.text()
        pdb = self.app.plugin(loadpdb.LoadPdb)

        self.setEnabled(False)

        if not self.app.menu("PDB").isEnabled():
            QtCore.QTimer.singleShot(100, self._onBtnParseClicked)
            return

        def _cb_table(res):
            self.setEnabled(True)
            if res is None:
                return
            model = self._load_table(res)
            model.toggleHexMode(self.ui.btnToggleHex.isChecked())
            model.toggleCharMode(self.ui.btnToggleChar.isChecked())
            if model.rowCount():
                p = ParseRecord(
                    struct=structname,
                    offset=self.ui.lineOffset.text(),
                    count=self.ui.spinParseCount.value(),
                    parse_mode="table",
                    model=model,
                )
                self.parse_hist.add_data(p)
                for c in range(model.columnCount()):
                    self.ui.tableView.resizeColumnToContents(c)

        def _cb_tree(res):
            self.setEnabled(True)
            if res is None:
                return
            model = self._load_tree(res)
            model.toggleHexMode(self.ui.btnToggleHex.isChecked())
            if model.rowCount():
                p = ParseRecord(
                    struct=structname,
                    offset=self.ui.lineOffset.text(),
                    count=self.ui.spinParseCount.value(),
                    parse_mode="tree",
                    model=model,
                )
                self.parse_hist.add_data(p)

        def _err(e, _):
            if isinstance(e, loadpdb.InvalidExpression):
                QtWidgets.QMessageBox.warning(
                    self,
                    "PDB Error!",
                    "Invalid expression: %r" % structname,
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "PDB Error!",
                    "Please load pdbin first!",
                )

        count = self.ui.spinParseCount.value()
        if self.ui.checkParseTable.isChecked():
            self.app.exec_async(
                pdb.parse_array,
                structname,
                addr=self.parse_offset,
                expr="",
                count=count,
                finished_cb=_cb_table,
                errored_cb=_err,
            )
        else:
            self.app.exec_async(
                pdb.parse_struct,
                structname,
                addr=self.parse_offset,
                expr=structname,
                count=count,
                add_dummy_root=True,
                finished_cb=_cb_tree,
                errored_cb=_err,
            )

    def _onParseHistoryClicked(self, data: ParseRecord):
        self.ui.lineStruct.setText(data.struct)
        self.ui.lineOffset.setText(data.offset)
        self.ui.spinParseCount.setValue(data.count or 1)
        self.ui.checkParseTable.setChecked(data.parse_mode == "table")
        self._onLineOffsetChanged()
        if data.model:
            if data.parse_mode == "table":
                self.ui.tableView.setModel(data.model)
                self.ui.stackedWidget.setCurrentWidget(self.ui.pageTable)
            else:
                self.ui.treeView.setModel(data.model)
                self.ui.stackedWidget.setCurrentWidget(self.ui.pageTree)

    def _load_tree(self, data: dict) -> qtmodel.StructTreeModel:
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageTree)
        model = qtmodel.StructTreeModel(data)
        model.toggleHexMode(self.ui.btnToggleHex.isChecked())
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

    def _load_table(self, data: list) -> qtmodel.StructTableModel:
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageTable)
        model = qtmodel.StructTableModel(data)
        model.toggleHexMode(self.ui.btnToggleHex.isChecked())
        if self.fileio:
            # TODO: global address fileio reader
            self.fileio.seek(self.parse_offset)
            model.loadStream(io.BytesIO(self.fileio.read()))
        self.ui.tableView.setModel(model)
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