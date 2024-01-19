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
from plugins import debugger
from plugins import loadpdb
from view import WidgetExpression
from view import resource


class Expression(QtWidgets.QWidget):
    def __init__(self, app: AppCtrl):
        super().__init__(app)
        self.ui = WidgetExpression.Ui_Form()
        self.ui.setupUi(self)
        set_app_title(self, "")

        self.app = app
        self.parse_hist = HistoryMenu(self.ui.btnHistory)
        self.parse_hist.actionTriggered.connect(self._onHistoryClicked)

        # event bindingd
        self.ui.lineStruct.returnPressed.connect(self._addExpression)
        self.ui.btnParse.clicked.connect(self._addExpression)

        self._init_ui()

    def _init_ui(self):
        pdb = self.app.plugin(loadpdb.LoadPdb)
        empty_struct = pdb.parse_struct("")
        model = qtmodel.StructTreeModel(empty_struct)
        model.subfieldsAsked.connect(self._lazy_load_item)
        self.ui.treeView.setModel(model)

    def _onHistoryClicked(self, val):
        self.ui.lineStruct.setText(val)

    def _addExpression(self):
        dbg = self.app.plugin(debugger.Debugger)
        pdb = self.app.plugin(loadpdb.LoadPdb)

        virt_base = dbg.get_virtual_base()
        if virt_base is None:
            rtn = QtWidgets.QMessageBox.warning(
                self,
                self.__class__.__name__,
                (
                    "You shall attach to a process before this operation.\n"
                    "Attach to current selected process and continue?"
                ),
                QtWidgets.QMessageBox.StandardButton.Yes,
                QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if rtn == QtWidgets.QMessageBox.StandardButton.Cancel:
                return
            else:
                self.app.run_cmd("AttachCurrentProcess", callback=self._addExpression)
                return
        expr = self.ui.lineStruct.text()

        def _cb(struct_record):
            self.ui.lineStruct.setEnabled(True)
            if struct_record is None:
                return
            self.parse_hist.add_data(expr)
            model = self.ui.treeView.model()
            if isinstance(model, qtmodel.StructTreeModel):
                model.loadStream(dbg.get_memory_stream())
                model.appendItem(struct_record)

        self.ui.lineStruct.setEnabled(False)
        self.app.exec_async(
            pdb.query_expression,
            expr=expr,
            virtual_base=virt_base,
            finished_cb=_cb,
        )

    def _lazy_load_item(self, parent, item: dict):
        dbg = self.app.plugin(debugger.Debugger)
        pdb = self.app.plugin(loadpdb.LoadPdb)
        model = self.ui.treeView.model()

        struct = item["lf"].utypeRef.name

        def _cb(struct_record):
            if struct_record is None:
                item["levelname"] = "load failed"
                return
            if isinstance(model, qtmodel.StructTreeModel):
                model.loadStream(dbg.get_memory_stream())
                item["fields"] = struct_record["fields"]
                model.setItem(item, parent)

        self.app.exec_async(
            pdb.parse_struct,
            structname=struct,
            expr=item["levelname"],
            addr=model.data(parent, QtCore.Qt.ItemDataRole.UserRole),
            finished_cb=_cb,
        )

if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    window = Expression(None)
    window.show()
    sys.exit(app.exec())