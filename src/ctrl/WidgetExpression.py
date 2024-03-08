import logging
import sys

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import HistoryMenu
from ctrl.qtapp import set_app_title
from helper import qtmodel
from modules.treesitter.expr_parser import InvalidExpression
from plugins import debugger
from plugins import loadpdb
from view import WidgetExpression

logger = logging.getLogger(__name__)


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
        self.ui.treeView.expanded.connect(lambda: self.ui.treeView.resizeColumnToContents(0))
        self.ui.btnToggleHex.clicked.connect(self._onBtnToggleHexClicked)
        self.ui.treeView.installEventFilter(self)
        self.ui.treeView.setItemDelegate(qtmodel.BorderItemDelegate())
        self.ui.treeView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.treeView.customContextMenuRequested.connect(self._onContextMenuOpened)

        self._init_ui()

    def _init_ui(self):
        pdb = self.app.plugin(loadpdb.LoadPdb)
        empty_struct = pdb.parse_expr_to_struct("")
        model = qtmodel.StructTreeModel(empty_struct)
        model.allow_dereferece_pointer = True
        model.pointerDereferenced.connect(self._lazy_load_pointer)
        model.pvoidStructChanged.connect(self._lazy_cast_pointer)
        self.ui.treeView.setModel(model)

    def eventFilter(self, obj: QtCore.QObject, evt: QtCore.QEvent) -> bool:
        if obj == self.ui.treeView:
            if evt.type() == QtCore.QEvent.Type.KeyPress:
                key = evt.key()
                indexes = [x for x in self.ui.treeView.selectedIndexes() if x.column() == 0]
                if key == QtCore.Qt.Key.Key_Delete:
                    if len(indexes) == 1:
                        # can only the delete top level structrue
                        if indexes[0].parent().isValid():
                            return False
                        model = self.ui.treeView.model()
                        model.removeRow(indexes[0].row(), indexes[0].parent())
        return False

    def _onHistoryClicked(self, val):
        self.ui.lineStruct.setText(val)

    def _addExpression(self):
        dbg = self.app.plugin(debugger.Debugger)
        pdb = self.app.plugin(loadpdb.LoadPdb)

        try:
            virt_base = dbg.get_virtual_base()
        except PermissionError as e:
            QtWidgets.QMessageBox.warning(
                self,
                self.__class__.__name__,
                str(e),
            )
            return
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
        logger.debug("Add: %r (Virtual Base = %s)" % (expr, hex(virt_base)))

        def _cb(struct_record):
            self.ui.lineStruct.setEnabled(True)
            if struct_record is None:
                return
            self.ui.lineStruct.setText("")
            self.parse_hist.add_data(expr)
            model = self.ui.treeView.model()
            if isinstance(model, qtmodel.StructTreeModel):
                model.loadStream(dbg.get_memory_stream())
                model.appendItem(struct_record)

        def _err(err, traceback):
            match err:
                case InvalidExpression():
                    QtWidgets.QMessageBox.warning(
                        self,
                        self.__class__.__name__,
                        "Invalid Expression: %s" % str(err),
                    )
                case _:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "PDB Error!",
                        repr(err),
                    )

        self.ui.lineStruct.setEnabled(False)
        self.app.exec_async(
            pdb.query_struct,
            expr=expr,
            virtual_base=virt_base,
            io_stream=dbg.get_memory_stream(),
            finished_cb=_cb,
            errored_cb=_err,
        )

    def _lazy_load_pointer(self, parent, address, count):
        dbg = self.app.plugin(debugger.Debugger)
        pdb = self.app.plugin(loadpdb.LoadPdb)
        model = self.ui.treeView.model()
        item = parent.internalPointer().copy()

        def _cb(struct_record):
            if struct_record is None:
                item["levelname"] = "load failed"
                return
            if isinstance(model, qtmodel.StructTreeModel):
                model.loadStream(dbg.get_memory_stream())
                item["fields"] = struct_record["fields"]
                model.setItem(item, parent)

        logger.debug("Expand: %r" % item["expr"])

        self.app.exec_async(
            pdb.deref_struct,
            struct=item,
            count=count,
            io_stream=dbg.get_memory_stream(),
            finished_cb=_cb,
        )

    def _lazy_cast_pointer(self, parent, address: int, count: int, ref_struct: str):
        dbg = self.app.plugin(debugger.Debugger)
        pdb = self.app.plugin(loadpdb.LoadPdb)
        model = self.ui.treeView.model()
        assert isinstance(model, qtmodel.StructTreeModel), "Only StructTreeModel available here"

        item = parent.internalPointer().copy()

        def _cb(struct_record):
            if struct_record is None:
                item["levelname"] = "load failed"
                model.setItem(item, parent)
                return
            model.loadStream(dbg.get_memory_stream())
            item["fields"] = struct_record["fields"]
            model.setItem(item, parent)

        def _err(err, traceback):
            match err:
                case InvalidExpression():
                    QtWidgets.QMessageBox.warning(
                        self,
                        self.__class__.__name__,
                        "Invalid Expression: %s" % str(err),
                    )
                case _:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "PDB Error!",
                        repr(err),
                    )
        logger.debug("Casting: '(%s)%s', Count = %d" % (item["type"], item["expr"], count))

        self.app.exec_async(
            pdb.deref_struct,
            struct=item,
            count=count,
            io_stream=dbg.get_memory_stream(),
            finished_cb=_cb,
            errored_cb=_err,
        )

    def _onBtnToggleHexClicked(self):
        model = self.ui.treeView.model()
        if isinstance(model, qtmodel.StructTreeModel):
            checked = self.ui.btnToggleHex.isChecked()
            model.toggleHexMode(checked)

    def _onContextMenuOpened(self, position):
        indexes = [i for i in self.ui.treeView.selectedIndexes() if i.column() == 0]
        model = self.ui.treeView.model()
        if not isinstance(model, qtmodel.StructTreeModel):
            return

        menu = QtWidgets.QMenu()
        if len(indexes) == 1:
            item = model.itemFromIndex(indexes[0])
            action = menu.addAction("Copy Expression")
            action.triggered.connect(lambda: QtGui.QGuiApplication.clipboard().setText(item["expr"]))

        menu.addSeparator()

        if len(indexes):
            action = menu.addAction("Refresh")
            action.setIcon(QtGui.QIcon(":icon/images/ctrl/Refresh_16x.svg"))
            action.triggered.connect(lambda: [model.refreshIndex(i) for i in indexes])

        menu.exec(self.ui.treeView.viewport().mapToGlobal(position))

    def refreshTree(self, index: QtCore.QModelIndex):
        index = index or QtCore.QModelIndex()
        model = self.ui.treeView.model()

        if isinstance(model, qtmodel.StructTreeModel):
            model.refreshIndex(index)

    def clearTree(self):
        model = self.ui.treeView.model()

        if isinstance(model, qtmodel.StructTreeModel):
            model.removeRows(0, model.rowCount())


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    window = Expression(None)
    window.show()
    sys.exit(app.exec())