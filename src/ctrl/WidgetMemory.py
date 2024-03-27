import io
import logging
import sys

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
        return "; ".join(data)


class Memory(QtWidgets.QWidget):
    def __init__(self, app: AppCtrl):
        super().__init__(app)
        self.ui = WidgetMemory.Ui_Form()
        self.ui.setupUi(self)
        set_app_title(self, "")

        self.app = app
        self.ui.btnHistory.setMenu(QtWidgets.QMenu())
        self.parse_hist = MemoryHistory(self.ui.btnHistory.menu())
        self.parse_hist.actionTriggered.connect(self._onHistoryClicked)

        # attributes
        self.buffer = io.BytesIO()

        self.ui.lineAddress.returnPressed.connect(self._loadMemory)
        self.ui.lineSize.returnPressed.connect(self._loadMemory)
        self.ui.tableMemory.setItemDelegate(qtmodel.BorderItemDelegate())

    def requestAddress(self) -> int:
        try:
            pdb = self.app.plugin(loadpdb.LoadPdb)
            dbg = self.app.plugin(debugger.Debugger)
            virt_base = dbg.get_virtual_base()
            stream = dbg.get_memory_stream()
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

    def requestSize(self) -> int:
        try:
            pdb = self.app.plugin(loadpdb.LoadPdb)
            dbg = self.app.plugin(debugger.Debugger)
            virt_base = dbg.get_virtual_base()
            stream = dbg.get_memory_stream()
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

    def _onHistoryClicked(self, val):
        addr, size = val
        self.ui.lineAddress.setText(addr)
        self.ui.lineSize.setText(size)

    def _loadMemory(self):
        dbg = self.app.plugin(debugger.Debugger)

        try:
            # test connection
            dbg.get_virtual_base()
        except PermissionError as e:
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

        mem = dbg.get_memory_stream()
        model = qtmodel.HexTable(mem)
        model.viewAddress = self.requestAddress()
        model.viewSize = self.requestSize()
        self.ui.tableMemory.setModel(model)
        self.ui.tableMemory.resizeColumnsToContents()
        self.ui.labelAddress.setText("Address: {}".format(model.addrPrefix[0]))
        self.parse_hist.add_data((self.ui.lineAddress.text(), self.ui.lineSize.text()))

    def dumpBuffer(self):
        dbg = self.app.plugin(debugger.Debugger)
        mem = dbg.get_memory_stream()
        model = self.ui.tableMemory.model()
        if not isinstance(model, qtmodel.HexTable):
            QtWidgets.QMessageBox.warning(
                self,
                self.__class__.__name__,
                tr("Not support dump memory from current model: %r") % model,
            )
            return

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            caption="Save bin as...",
            filter="Bin (*.bin);; Any (*.*)",
        )
        if filename:
            mem.seek(model.viewAddress)
            try:
                data = mem.read(model.viewSize)
                with open(filename, "wb") as fs:
                    fs.write(data)
                err = None
            except Exception as e:
                err = e
            if err is None:
                QtWidgets.QMessageBox.information(
                    self,
                    self.__class__.__name__,
                    tr("Successfully dump memory to\n%r") % filename,
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.__class__.__name__,
                    str(err),
                )


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    window = Memory(None)
    window.show()
    sys.exit(app.exec())