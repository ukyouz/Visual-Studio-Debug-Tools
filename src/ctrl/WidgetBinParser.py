import io
import logging
import os
import sys
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Literal
from typing import Optional

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import AutoRefreshTimer
from ctrl.qtapp import HistoryMenu
from ctrl.qtapp import set_app_title
from helper import qtmodel
from modules.expr_parser import InvalidExpression
from modules.utils.typ import Stream
from plugins import loadpdb
from view import WidgetBinParser

logger = logging.getLogger(__name__)


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
    def __init__(self, app: AppCtrl):
        super().__init__(app)
        self.app = app
        self.fileio = None
        self.ui = WidgetBinParser.Ui_Form()
        self.ui.setupUi(self)
        set_app_title(self, "")

        # properties
        self.ui.btnHistory.setMenu(QtWidgets.QMenu())
        self.parse_hist = ParseHistoryMenu(self.ui.btnHistory.menu())
        self.parse_hist.actionTriggered.connect(self._onParseHistoryClicked)
        self.viewAddress = 0
        self.viewSize = -1

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
        self.ui.treeView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.treeView.customContextMenuRequested.connect(lambda p: self._onContextMenuOpened(p, self.ui.treeView))
        self.ui.tableMemory.setItemDelegate(qtmodel.BorderItemDelegate())
        self.ui.tableView.installEventFilter(self)
        self.ui.tableView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.tableView.customContextMenuRequested.connect(lambda p: self._onContextMenuOpened(p, self.ui.tableView))
        self.ui.tableView.horizontalHeader().setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.tableView.horizontalHeader().customContextMenuRequested.connect(self._onHorizontalContextMenuOpened)
        self.ui.tableView.verticalHeader().setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.tableView.verticalHeader().customContextMenuRequested.connect(self._onVerticalContextMenuOpened)

        self._var_watcher = {
            "tree": AutoRefreshTimer(self, self.ui.treeView),
            "table": AutoRefreshTimer(self, self.ui.tableView),
        }

    @property
    def var_watcher(self):
        tab = self.ui.stackedWidget.currentWidget()
        if tab == self.ui.pageTree:
            return self._var_watcher["tree"]
        else:
            return self._var_watcher["table"]

    @property
    def streamSize(self):
        if self.viewSize > 0:
            return self.viewSize
        elif self.fileio:
            self.fileio.seek(0, os.SEEK_END)
            return self.fileio.tell()
        else:
            return 0

    def eventFilter(self, obj: QtCore.QObject, evt: QtCore.QEvent) -> bool:
        if obj == self.ui.tableView:
            model = self.ui.tableView.model()
            selected_indexes = self.ui.tableView.selectedIndexes()
            if evt.type() == QtCore.QEvent.Type.KeyPress:
                key = evt.key()
                modifiers = evt.modifiers()
                ctrl = modifiers & QtCore.Qt.KeyboardModifier.ControlModifier
                if ctrl and key == ord("C"):
                    if len(selected_indexes) > 1:
                        if isinstance(model, qtmodel.StructTableModel):
                            txt = model.getTextFromIndexes(selected_indexes)
                            cb = QtGui.QGuiApplication.clipboard()
                            cb.setText(txt, mode=cb.Clipboard)
                            return True
        return False

    def closeEvent(self, e: QtGui.QCloseEvent) -> None:
        rtn = self.var_watcher.onClosing()
        if rtn is None:
            if getattr(self.fileio, "name", None) is not None:
                # expect a file (ie. sent from BinView), so just let it go
                e.accept()
                return

            # expect memory on ram (ie. sent from VS Debugger)
            # need to warn user for closing a view
            models = (
                self.ui.treeView.model(),
                self.ui.tableView.model(),
            )
            if any(m.rowCount() for m in models if m):
                rtn = QtWidgets.QMessageBox.warning(
                    self,
                    self.__class__.__name__,
                    self.tr("View is not empty, Ok to close?"),
                    QtWidgets.QMessageBox.StandardButton.Yes,
                    QtWidgets.QMessageBox.StandardButton.Cancel,
                )

        if rtn == QtWidgets.QMessageBox.StandardButton.Cancel:
            e.ignore()
        else:
            e.accept()

    def export_as_csv(self):
        rtn = self.var_watcher.onAnyRelatedOperating()
        if rtn == QtWidgets.QMessageBox.StandardButton.Cancel:
            return

        if self.fileio:
            filename = getattr(self.fileio, "name", "noname")
            bin_fname = "/" + str(Path(filename).with_suffix(".csv"))
        else:
            bin_fname = ""
        dialog = QtWidgets.QFileDialog(self)
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            caption=self.tr("Save as csv..."),
            directory=dialog.directory().filePath(bin_fname),
            filter="CSV files (*.csv);; Any (*.*)"
        )
        if filename:
            page = self.ui.stackedWidget.currentWidget()
            if page is self.ui.pageTable:
                model = self.ui.tableView.model()
                if isinstance(model, qtmodel.StructTableModel):
                    txt = model.getTextFromIndexes()
                    try:
                        with open(filename, "w") as fs:
                            fs.write(txt)
                        QtWidgets.QMessageBox.information(
                            self,
                            self.__class__.__name__,
                            self.tr("Successfully exported table!\n%r") % filename,
                        )
                    except Exception as e:
                        QtWidgets.QMessageBox.warning(
                            self,
                            self.__class__.__name__,
                            self.tr("Error exported file! %s") % e,
                        )

    @property
    def parse_offset(self):
        try:
            pdb = self.app.plugin(loadpdb.LoadPdb)
            return int(pdb.query_cstruct(self.ui.lineOffset.text(), io_stream=self.fileio))
        except ValueError as e:
            logger.warning("Offset: {}".format(e))
            return 0
        except InvalidExpression as e:
            logger.warning("Offset: {}".format(e))
            return 0
        except Exception as e:
            logger.warning(e, exc_info=True)
            return 0

    def loadFile(self, fileio: Stream):
        self.fileio = fileio
        set_app_title(self, getattr(fileio, "name", "noname"))
        tblmodel = qtmodel.HexTable(fileio, self.ui.tableMemory)
        tblmodel.viewAddress = self.viewAddress
        tblmodel.viewSize = self.viewSize
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

        rtn = self.var_watcher.onAnyRelatedOperating()
        if rtn == QtWidgets.QMessageBox.StandardButton.Cancel:
            return

        self.setEnabled(False)

        if pdb.is_loading():
            QtCore.QTimer.singleShot(100, self._onBtnParseClicked)
            return

        def _cb_table(res):
            self.setEnabled(True)
            if res is None:
                return
            model = self._load_table(res)
            model.toggleHexMode(self.ui.btnToggleHex.isChecked())
            model.toggleCharMode(self.ui.btnToggleChar.isChecked())
            self.ui.btnToggleChar.setEnabled(True)
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
            self.ui.btnToggleChar.setEnabled(False)
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
                    self.tr("PDB Error!"),
                    self.tr("Invalid expression: %r") % structname,
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.tr("PDB Error!"),
                    self.tr("Please load pdbin first!"),
                )

        count = self.ui.spinParseCount.value()

        if self.ui.checkParseTable.isChecked():
            self.app.exec_async(
                pdb.parse_expr_to_table,
                structname,
                addr=self.viewAddress + self.parse_offset,
                count=count,
                data_size=self.streamSize,
                finished_cb=_cb_table,
                errored_cb=_err,
            )
        else:
            self.app.exec_async(
                pdb.parse_expr_to_struct,
                structname,
                addr=self.viewAddress + self.parse_offset,
                count=count,
                data_size=self.viewAddress + self.streamSize,
                add_dummy_root=True,
                finished_cb=_cb_tree,
                errored_cb=_err,
            )

    def _onParseHistoryClicked(self, data: ParseRecord):
        rtn = self.var_watcher.onAnyRelatedOperating()
        if rtn == QtWidgets.QMessageBox.StandardButton.Cancel:
            return

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
        model.allow_edit_top_expr = False
        model.toggleHexMode(self.ui.btnToggleHex.isChecked())
        if self.fileio:
            model.loadStream(self.fileio)
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
            model.loadStream(self.fileio)
        self.ui.tableView.setModel(model)
        return model

    def _onHorizontalContextMenuOpened(self, position):
        indexes = self.ui.tableView.selectedIndexes()
        if not indexes:
            return
        model = self.ui.tableView.model()
        if not isinstance(model, qtmodel.StructTableModel):
            return

        menu = QtWidgets.QMenu()

        if self.app.__class__.__name__ == "VisualStudioDebugger":
            action = menu.addAction(self.tr("Refresh"))
            action.setIcon(QtGui.QIcon(":icon/images/ctrl/Refresh_16x.svg"))
            action.triggered.connect(lambda: [model.dataChanged.emit(i, i) for i in indexes])

            submenu = self.var_watcher.createContextMenues(indexes)
            menu.addMenu(submenu)

        menu.exec(self.ui.tableView.horizontalHeader().viewport().mapToGlobal(position))

    def _onVerticalContextMenuOpened(self, position):
        indexes = self.ui.tableView.selectedIndexes()
        if not indexes:
            return
        model = self.ui.tableView.model()
        if not isinstance(model, qtmodel.StructTableModel):
            return

        menu = QtWidgets.QMenu()

        if self.app.__class__.__name__ == "VisualStudioDebugger":
            action = menu.addAction(self.tr("Refresh"))
            action.setIcon(QtGui.QIcon(":icon/images/ctrl/Refresh_16x.svg"))
            action.triggered.connect(lambda: [model.dataChanged.emit(i, i) for i in indexes])

            submenu = self.var_watcher.createContextMenues(indexes)
            menu.addMenu(submenu)

        menu.exec(self.ui.tableView.verticalHeader().viewport().mapToGlobal(position))

    def _onContextMenuOpened(self, position, view):
        indexes = view.selectedIndexes()
        if not indexes:
            return
        model = self.ui.tableView.model()
        if not isinstance(model, qtmodel.StructTableModel):
            return

        menu = QtWidgets.QMenu()

        if self.app.__class__.__name__ == "VisualStudioDebugger":
            action = menu.addAction(self.tr("Refresh"))
            action.setIcon(QtGui.QIcon(":icon/images/ctrl/Refresh_16x.svg"))
            action.triggered.connect(lambda: [model.dataChanged.emit(i, i) for i in indexes])

            submenu = self.var_watcher.createContextMenues(indexes)
            menu.addMenu(submenu)

        menu.exec(view.viewport().mapToGlobal(position))

    def focusParseResult(self):
        self.ui.splitter.setSizes([1, 0])

    def setStruct(self, name: str):
        self.ui.lineStruct.setText(name)


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
    window = BinParser(None)
    window.loadFile(fileio)
    window.show()
    sys.exit(app.exec())