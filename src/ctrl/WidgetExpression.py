import functools
import logging
import sys

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import AutoRefreshTimer
from ctrl.qtapp import HistoryMenu
from ctrl.qtapp import set_app_title
from helper import qtmodel
from modules.treesitter.expr_parser import InvalidExpression
from plugins import debugger
from plugins import dock
from plugins import loadpdb
from view import WidgetExpression

logger = logging.getLogger(__name__)


def _err(self, err, traceback):
    match err:
        case InvalidExpression():
            QtWidgets.QMessageBox.warning(
                self,
                self.__class__.__name__,
                self.tr("Invalid Expression: %s") % str(err),
            )
        case _:
            QtWidgets.QMessageBox.warning(
                self,
                self.tr("PDB Error!"),
                repr(err),
            )


class Expression(QtWidgets.QWidget):
    def __init__(self, app: AppCtrl, dbg: debugger.Debugger):
        super().__init__(app)
        self.ui = WidgetExpression.Ui_Form()
        self.ui.setupUi(self)
        set_app_title(self, "")

        self.app = app
        self.debugger = dbg
        self.ui.btnHistory.setMenu(QtWidgets.QMenu())
        self.parse_hist = HistoryMenu(self.ui.btnHistory.menu())
        self.parse_hist.actionTriggered.connect(self._onHistoryClicked)

        # event bindingd
        self.installEventFilter(self)
        self.ui.lineStruct.returnPressed.connect(self._addExpression)
        self.ui.btnParse.clicked.connect(self._addExpression)
        # self.ui.treeView.expanded.connect(lambda: self.ui.treeView.resizeColumnToContents(0))
        self.ui.btnToggleHex.toggled.connect(self._onBtnToggleHexClicked)
        self.ui.treeView.installEventFilter(self)
        self.ui.treeView.setItemDelegate(qtmodel.BorderItemDelegate())
        self.ui.treeView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.treeView.customContextMenuRequested.connect(self._onContextMenuOpened)

        self._init_ui()

        self.var_watcher = AutoRefreshTimer(self, self.ui.treeView)
        self.var_watcher.timeOut.connect(self._onAutoRefreshTimeout)

    def _init_ui(self):
        pdb = self.app.plugin(loadpdb.LoadPdb)
        empty_struct = pdb.parse_expr_to_struct("")
        model = qtmodel.StructTreeModel(empty_struct)
        model.allow_dereferece_pointer = True
        model.pointerDereferenced.connect(self._lazy_load_pointer)
        model.pvoidStructChanged.connect(functools.partial(self._lazy_load_pointer, casting=True))
        model.exprChanged.connect(self._change_expr)
        self.ui.treeView.setModel(model)

    def eventFilter(self, obj: QtCore.QObject, evt: QtCore.QEvent) -> bool:
        if evt.type() != QtCore.QEvent.Type.KeyPress:
            return False

        key = evt.key()
        modifiers = evt.modifiers()
        NO = QtCore.Qt.KeyboardModifier.NoModifier
        CTRL = QtCore.Qt.KeyboardModifier.ControlModifier
        ALT = QtCore.Qt.KeyboardModifier.AltModifier

        if obj == self.ui.treeView:
            indexes = [x for x in self.ui.treeView.selectedIndexes() if x.column() == 0]
            match (modifiers, key):
                case (NO, QtCore.Qt.Key.Key_Delete):
                    if len(indexes) == 1:
                        # can only the delete top level structrue
                        if indexes[0].parent().isValid():
                            return False
                        rtn = self.var_watcher.onDeleting()
                        if rtn == QtWidgets.QMessageBox.StandardButton.Cancel:
                            return True
                        model = self.ui.treeView.model()
                        model.removeRow(indexes[0].row(), indexes[0].parent())
                        return True
        else:
            match (modifiers, key):
                case (CTRL, QtCore.Qt.Key.Key_L):
                    self.ui.lineStruct.setFocus()
                    return True
                case (ALT, QtCore.Qt.Key.Key_X):
                    checked = self.ui.btnToggleHex.isChecked()
                    self.ui.btnToggleHex.setChecked(not checked)

        return False

    def closeEvent(self, e: QtGui.QCloseEvent):
        model = self.ui.treeView.model()
        rtn = self.var_watcher.onClosing()
        if rtn is None:
            if model is not None and model.rowCount():
                rtn = QtWidgets.QMessageBox.warning(
                    self,
                    self.__class__.__name__,
                    self.tr("View is not empty, Ok to close?"),
                    QtWidgets.QMessageBox.StandardButton.Ok,
                    QtWidgets.QMessageBox.StandardButton.Cancel,
                )

        if rtn == QtWidgets.QMessageBox.StandardButton.Cancel:
            e.ignore()
            return
        e.accept()

    def _onHistoryClicked(self, val):
        self.ui.lineStruct.setText(val)

    def _onAutoRefreshTimeout(self, i):
        model = self.ui.treeView.model()
        if not isinstance(model, qtmodel.StructTreeModel):
            return
        if model.rowCount(i) == 0:
            # to avoid logging too much things, only log the specific data having no children item
            item = model.itemFromIndex(i)
            expr = item["expr"]
            value = item["value"]
            self.app.log(f"{expr} = {value} ({value:#x})")

    def _try_get_virtual_base(self, cb=None) -> int | None:
        try:
            return self.debugger.get_virtual_base()
        except OSError as e:
            QtWidgets.QMessageBox.warning(
                self,
                self.__class__.__name__,
                str(e),
            )
        except debugger.ProcessNotConnected:
            if not callable(cb):
                return

            rtn = QtWidgets.QMessageBox.warning(
                self,
                self.__class__.__name__,
                self.tr(
                    "You shall attach to a process before this operation.\n"
                    "Attach to current selected process and continue?"
                ),
                QtWidgets.QMessageBox.StandardButton.Yes,
                QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if rtn == QtWidgets.QMessageBox.StandardButton.Yes:
                cb()

    def _addExpression(self):
        pdb = self.app.plugin(loadpdb.LoadPdb)

        def cb():
            self.app.run_cmd("AttachCurrentProcess", callback=self._addExpression)

        virt_base = self._try_get_virtual_base(cb)
        if virt_base is None:
            return

        expr = self.ui.lineStruct.text()

        if expr == "":
            return

        logger.debug("Add: %r (Virtual Base = %s)" % (expr, hex(virt_base)))

        def _cb(struct_record):
            if struct_record is None:
                return
            self.ui.lineStruct.setText("")
            self.parse_hist.add_data(expr)
            model = self.ui.treeView.model()
            if isinstance(model, qtmodel.StructTreeModel):
                model.loadStream(self.debugger.get_memory_stream())
                model.appendItem(struct_record)
            for c in range(2, model.columnCount()):
                self.ui.treeView.resizeColumnToContents(c)

        self.app.exec_async(
            pdb.query_struct,
            expr=expr,
            virtual_base=virt_base,
            io_stream=self.debugger.get_memory_stream(),
            finished_cb=_cb,
            errored_cb=functools.partial(_err, self),
            block_UIs=[
                self.ui.lineStruct,
                self.ui.treeView,
            ],
        )

    def _change_expr(self, parent):
        pdb = self.app.plugin(loadpdb.LoadPdb)
        model = self.ui.treeView.model()
        item = parent.internalPointer()

        virt_base = self._try_get_virtual_base()
        if virt_base is None:
            return

        def _cb(struct_record):
            if struct_record is None:
                item["_is_invalid"] = True
                return
            item["_is_invalid"] = False
            if isinstance(model, qtmodel.StructTreeModel):
                model.loadStream(self.debugger.get_memory_stream())
                model.setItem(struct_record, parent)

        logger.debug("Expand: %r" % item["expr"])

        self.app.exec_async(
            pdb.query_struct,
            expr=item["expr"],
            virtual_base=virt_base,
            io_stream=self.debugger.get_memory_stream(),
            finished_cb=_cb,
            errored_cb=functools.partial(_err, self),
            block_UIs=[
                self.ui.treeView,
            ],
        )

    def _lazy_load_pointer(self, parent, count, casting=False):
        pdb = self.app.plugin(loadpdb.LoadPdb)
        item = parent.internalPointer().copy()

        virt_base = self._try_get_virtual_base()
        if virt_base is None:
            return

        def _cb(struct_record):
            model = self.ui.treeView.model()
            assert isinstance(model, qtmodel.StructTreeModel), "Only StructTreeModel available here"
            if struct_record is None:
                empty_struct = pdb.parse_expr_to_struct("")
                empty_struct["_is_invalid"] = True
                empty_struct["is_pointer"] = False
                empty_struct["levelname"] = "> err: load failed!"
                item["fields"] = [empty_struct]
                model.setItem(item, parent)
                return
            model.loadStream(self.debugger.get_memory_stream())
            item["fields"] = struct_record["fields"]
            model.setItem(item, parent)

        logger.debug("Expand: '(%s)%s', Count = %d" % (item["type"], item["expr"], count))

        if item.get("is_funcptr", False):
            self.app.exec_async(
                pdb.deref_function_pointer,
                struct=item,
                io_stream=self.debugger.get_memory_stream(),
                virtual_base=virt_base,
                finished_cb=_cb,
                errored_cb=functools.partial(_err, self),
                block_UIs=[
                    self.ui.treeView,
                ],
            )
        else:
            self.app.exec_async(
                pdb.deref_struct,
                struct=item,
                count=count,
                io_stream=self.debugger.get_memory_stream(),
                casting=casting,
                finished_cb=_cb,
                errored_cb=functools.partial(_err, self),
                block_UIs=[
                    self.ui.treeView,
                ],
            )

    def _onBtnToggleHexClicked(self, checked: bool):
        model = self.ui.treeView.model()
        if isinstance(model, qtmodel.StructTreeModel):
            model.toggleHexMode(checked)

    def _onContextMenuOpened(self, position):
        indexes = [i for i in self.ui.treeView.selectedIndexes() if i.column() == 0]
        model = self.ui.treeView.model()
        if not isinstance(model, qtmodel.StructTreeModel):
            return

        menu = QtWidgets.QMenu()
        if len(indexes) == 1:
            item = model.itemFromIndex(indexes[0])
            action = menu.addAction(self.tr("Copy Expression"))
            action.triggered.connect(lambda: QtGui.QGuiApplication.clipboard().setText(item["expr"]))

        menu.addSeparator()

        if len(indexes):
            action = menu.addAction(self.tr("Refresh"))
            action.setIcon(QtGui.QIcon(":icon/images/ctrl/Refresh_16x.svg"))
            action.triggered.connect(lambda: [model.refreshIndex(i) for i in indexes])

            submenu = self.var_watcher.createContextMenues(indexes)
            menu.addMenu(submenu)

        menu.addSeparator()

        if len(indexes) == 1:
            action = menu.addAction(self.tr("Show in BinParser"))
            # action.setIcon(QtGui.QIcon(":icon/images/ctrl/Refresh_16x.svg"))
            item = model.itemFromIndex(indexes[0])
            action.triggered.connect(functools.partial(self._openBinParserFromExpression, item))

        menu.exec(self.ui.treeView.viewport().mapToGlobal(position))

    def _openBinParserFromExpression(self, item):
        _d = self.app.plugin(dock.Dock)
        b = _d.addBinParserView(
            item["address"],
            item["size"],
        )
        b.setWindowTitle(item["expr"])

    def readBuffer(self, item: loadpdb.ViewStruct) -> bytes:
        stream = self.debugger.get_memory_stream()
        stream.seek(item["address"])
        return stream.read(item["size"])

    def refreshTree(self, index: QtCore.QModelIndex):
        index = index or QtCore.QModelIndex()
        model = self.ui.treeView.model()

        if isinstance(model, qtmodel.StructTreeModel):
            model.refreshIndex(index)

    def clearTree(self):
        rtn = self.var_watcher.onDeleting()
        if rtn == QtWidgets.QMessageBox.StandardButton.Cancel:
            return
        if self.var_watcher.clearAutoRefresh():
            QtCore.QTimer.singleShot(100, self.clearTree)
        else:
            model = self.ui.treeView.model()
            if isinstance(model, qtmodel.StructTreeModel):
                model.removeRows(0, model.rowCount())


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    window = Expression(None, None)
    window.show()
    sys.exit(app.exec())