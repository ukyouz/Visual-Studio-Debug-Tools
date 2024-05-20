import logging
import sys
from contextlib import suppress

from PyQt6 import QtGui
from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import HistoryMenu
from ctrl.qtapp import i18n
from ctrl.qtapp import set_app_title
from helper import qtmodel
from modules.treesitter.expr_parser import InvalidExpression
from plugins import debugger
from plugins import loadpdb
from view import WidgetMemory

tr = lambda txt: i18n("Memory", txt)
logger = logging.getLogger(__name__)


class MemoryHistory(HistoryMenu):
    def stringify(self, data: tuple[str, str]) -> str:
        addr, size = data
        if size:
            return "{} +{}".format(addr, size)
        else:
            return addr


class Memory(QtWidgets.QWidget):
    def __init__(self, app: AppCtrl, dbg: debugger.Debugger):
        super().__init__(app)
        self.ui = WidgetMemory.Ui_Form()
        self.ui.setupUi(self)
        set_app_title(self, "")

        self.app = app
        self.debugger = dbg
        self.ui.btnHistory.setMenu(QtWidgets.QMenu())
        self.parse_hist = MemoryHistory(self.ui.btnHistory.menu())
        self.parse_hist.actionTriggered.connect(self._onHistoryClicked)

        self.ui.lineAddress.returnPressed.connect(self._loadMemory)
        self.ui.lineSize.returnPressed.connect(self._loadMemory)
        self.ui.comboItemColumn.currentTextChanged.connect(self._onItemColumnChanged)
        self.ui.comboItemSize.currentIndexChanged.connect(self._onItemColumnSize)
        self.ui.tableMemory.setItemDelegate(qtmodel.BorderItemDelegate())
        header = self.ui.tableMemory.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)


    def closeEvent(self, e: QtGui.QCloseEvent) -> None:
        model = self.ui.tableMemory.model()
        if model is not None and model.rowCount():
            rtn = QtWidgets.QMessageBox.warning(
                self,
                self.__class__.__name__,
                tr("View is not empty, Ok to close?"),
                QtWidgets.QMessageBox.StandardButton.Yes,
                QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if rtn == QtWidgets.QMessageBox.StandardButton.Cancel:
                e.ignore()
                return
        e.accept()

    def inputAddress(self) -> int:
        with suppress(Exception):
            return eval(self.ui.lineAddress.text())
        try:
            pdb = self.app.plugin(loadpdb.LoadPdb)
            virt_base = self.debugger.get_virtual_base()
            stream = self.debugger.get_memory_stream()
            return int(pdb.query_cstruct(self.ui.lineAddress.text(), virt_base, stream))
        except InvalidExpression as e:
            QtWidgets.QMessageBox.warning(
                self,
                self.__class__.__name__,
                tr("Invalid Expression: %s") % str(e),
            )
            logger.warning(e)
            return 0
        except Exception as e:
            logger.warning(e)
            return 0

    def requestedAddress(self) -> int:
        model = self.ui.tableMemory.model()
        if not isinstance(model,  qtmodel.HexTable):
            raise qtmodel.ModelNotSupportError(tr("No memory is loaded yet!"))
        return model.viewAddress

    def requestedSize(self) -> int:
        model = self.ui.tableMemory.model()
        if not isinstance(model,  qtmodel.HexTable):
            raise qtmodel.ModelNotSupportError(tr("No memory is loaded yet!"))
        return model.viewSize

    def inputSize(self) -> int:
        with suppress(Exception):
            return eval(self.ui.lineSize.text())
        try:
            pdb = self.app.plugin(loadpdb.LoadPdb)
            virt_base = self.debugger.get_virtual_base()
            stream = self.debugger.get_memory_stream()
            return int(pdb.query_cstruct(self.ui.lineSize.text(), virt_base, stream))
        except InvalidExpression as e:
            QtWidgets.QMessageBox.warning(
                self,
                self.__class__.__name__,
                tr("Invalid Expression: %s! Use default size: 1024.") % str(e),
            )
            logger.warning(e)
            return 1024
        except Exception as e:
            logger.warning(e)
            return 1024

    @property
    def itemColumn(self) -> int:
        try:
            return eval(self.ui.comboItemColumn.currentText())
        except Exception:
            return 4

    @property
    def itemSize(self) -> int:
        current_id = self.ui.comboItemSize.currentIndex()
        return 2 ** current_id

    def _onItemColumnChanged(self, val: str):
        model = self.ui.tableMemory.model()
        if not isinstance(model, qtmodel.HexTable):
            return
        model.column = self.itemColumn
        model.refresh()

    def _onItemColumnSize(self, val: int):
        model = self.ui.tableMemory.model()
        if not isinstance(model, qtmodel.HexTable):
            return
        model.itembyte = self.itemSize
        model.refresh()

    def _onHistoryClicked(self, val):
        addr, size = val
        self.ui.lineAddress.setText(addr)
        self.ui.lineSize.setText(size)

    def _loadMemory(self):
        try:
            # test connection
            self.debugger.get_virtual_base()
        except OSError as e:
            QtWidgets.QMessageBox.warning(
                self,
                self.__class__.__name__,
                str(e),
            )
            return
        except debugger.ProcessNotConnected:
            rtn = QtWidgets.QMessageBox.warning(
                self,
                self.__class__.__name__,
                tr(
                    "You shall attach to a process before this operation.\n"
                    "Attach to current selected process and continue?"
                ),
                QtWidgets.QMessageBox.StandardButton.Yes,
                QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if rtn == QtWidgets.QMessageBox.StandardButton.Cancel:
                return
            else:
                self.app.run_cmd("AttachCurrentProcess", callback=self._loadMemory)
                return

        mem = self.debugger.get_memory_stream()
        addr = self.inputAddress()
        model = qtmodel.HexTable(mem)
        model.viewAddress = addr
        model.viewSize = self.inputSize()
        model.column = self.itemColumn
        model.itembyte = self.itemSize
        self.ui.tableMemory.setModel(model)
        self.ui.tableMemory.resizeColumnsToContents()
        self.ui.labelAddress.setText("Address: {}".format(model.addrPrefix[0]))
        self.parse_hist.add_data((self.ui.lineAddress.text(), self.ui.lineSize.text()))

        set_app_title(self, "M-{:#08x}".format(addr))

    def readBuffer(self) -> bytes:
        mem = self.debugger.get_memory_stream()
        model = self.ui.tableMemory.model()
        if not isinstance(model, qtmodel.HexTable):
            raise qtmodel.ModelNotSupportError(tr("Not support read memory from current model: %r") % model)

        mem.seek(model.viewAddress)
        return mem.read(model.viewSize)

    def dumpBuffer(self):
        try:
            data = self.readBuffer()
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                caption=tr("Save bin as..."),
                filter="Bin (*.bin);; Any (*.*)",
            )
            if filename:
                with open(filename, "wb") as fs:
                    fs.write(data)
        except Exception as err:
            QtWidgets.QMessageBox.warning(
                self,
                self.__class__.__name__,
                str(err),
            )
        else:
            # Successful case
            QtWidgets.QMessageBox.information(
                self,
                self.__class__.__name__,
                tr("Successfully dump memory to\n%r") % filename,
            )

if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    window = Memory(None, None)
    window.show()
    sys.exit(app.exec())