from collections import defaultdict
from functools import partial

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from ctrl.qtapp import MenuAction
from ctrl.qtapp import Plugin
from ctrl.WidgetBinParser import BinParser
from ctrl.WidgetDockTitleBar import DockTitleBar
from ctrl.WidgetExpression import Expression
from ctrl.WidgetMemory import Memory
from helper import qtmodel
from plugins import debugger


class Dock(Plugin):
    def registerMenues(self) -> list[MenuAction]:
        return [
            {
                "name": self.tr("Debugger"),
                "submenus": [
                    {
                        "name": self.tr("Add Memory View"),
                        "command": "AddMemoryView",
                        "icon": ":icon/images/ctrl/Memory_16x.svg",
                    },
                    {
                        "name": self.tr("Add Expression View"),
                        "command": "AddExpressionView",
                        "icon": ":icon/images/ctrl/VariableExpression_16x.svg",
                    },
                ],
            },
        ]

    def registerCommands(self) -> list[tuple]:
        return [
            ("AddMemoryView", self.addMemoryView),
            ("AddExpressionView", self.addExpressionView),
        ]

    def post_init(self):
        self.docks = defaultdict(dict)
        self.app.evt.add_hook("ApplicationClosed", self._onClosed)

    def load_plugins(self, dbg: debugger.Debugger):
        self._dbg = dbg

    def init_views(self):
        # initialize dock widgets
        de = self.addExpressionView()
        dm = self.addMemoryView()

        width = self.app.size().width()
        opts = self.app.dockOptions()
        self.app.setDockOptions(opts | QtWidgets.QMainWindow.DockOption.GroupedDragging)
        self.app.resizeDocks([dm], [width * 2 // 3], QtCore.Qt.Orientation.Horizontal)
        self.app.tabifyDockWidget(dm, de)

    def _onClosed(self, evt):
        for docks in self.docks.values():
            for d in docks.keys():
                d.close()

    def _rename_dockwidget(self, dockwidget):
        txt, done = QtWidgets.QInputDialog.getText(
            dockwidget,
            self.app.__class__.__name__,
            self.tr("Input a new name for [%s]") % dockwidget.windowTitle(),
            text=dockwidget.windowTitle(),
        )
        if done:
            dockwidget.setWindowTitle(txt)

    def generate_dockwidget(self):
        dockWidget = QtWidgets.QDockWidget(parent=self.app)
        # dockWidget.setObjectName("dockWidget")
        dockWidget.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable
            |QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable
            # |QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        titlebar = DockTitleBar(dockWidget)
        dockWidget.setTitleBarWidget(titlebar)
        dockWidget.setContentsMargins(0, 0, 0, 0)
        menu = QtWidgets.QMenu()
        self._addAction(menu, self.tr("Rename tab"), lambda: self._rename_dockwidget(dockWidget))
        titlebar.ui.btnMore.setMenu(menu)
        return dockWidget

    def _addAction(self, menu, title, cb=None):
        action = menu.addAction(title)
        if cb:
            action.triggered.connect(cb)
        return action

    def _close_dock(self, dockWidget: QtWidgets.QDockWidget, widget_dict: dict):
        ok = True
        if w := dockWidget.widget():
            ok = w.close()
        if not ok:
            return
        self.app.removeDockWidget(dockWidget)
        del widget_dict[dockWidget]

    def addExpressionView(self) -> QtWidgets.QDockWidget:
        dockWidget = self.generate_dockwidget()
        dockWidget.setWindowIcon(QtGui.QIcon(":icon/images/ctrl/VariableExpression_16x.svg"))
        expr = Expression(self.app, self._dbg)
        self.docks["expression"][dockWidget] = expr
        dockWidget.setWidget(expr)
        dockWidget.setWindowTitle("Expression-%d" % len(self.docks["expression"]))
        self.app.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dockWidget)

        titlebar = dockWidget.titleBarWidget()
        if isinstance(titlebar, DockTitleBar):
            titlebar.ui.btnClose.clicked.connect(lambda: self._close_dock(dockWidget, self.docks["expression"]))

            menu = titlebar.ui.btnMore.menu()

            action = self._addAction(menu, self.tr("Editable top expression"))
            def _toggle_editable_top_node(checked: bool):
                model = expr.ui.treeView.model()
                if isinstance(model, qtmodel.StructTreeModel):
                    model.allow_edit_top_expr = checked
            action.toggled.connect(_toggle_editable_top_node)
            action.setCheckable(True)
            action.setChecked(True)

            menu.addSeparator()

            action = self._addAction(menu, self.tr("Refresh"), expr.refreshTree)
            action.setIcon(QtGui.QIcon(":icon/images/ctrl/Refresh_16x.svg"))

            action = self._addAction(menu, self.tr("Stop All Auto Refresh Timers"), expr.var_watcher.clearAutoRefresh)
            action.setIcon(QtGui.QIcon(":icon/images/vswin2019/Timeout_16x.svg"))

            menu.addSeparator()

            action = self._addAction(menu, self.tr("Clear expressions"), expr.clearTree)

            menu.addSeparator()

            action = self._addAction(menu, self.tr("Add Expression View"), self.addExpressionView)
            action.setIcon(QtGui.QIcon(":icon/images/ctrl/VariableExpression_16x.svg"))

        return dockWidget

    def addMemoryView(self) -> QtWidgets.QDockWidget:
        dockWidget = self.generate_dockwidget()
        dockWidget.setWindowIcon(QtGui.QIcon(":icon/images/ctrl/Memory_16x.svg"))
        mem = Memory(self.app, self._dbg)
        self.docks["memory"][dockWidget] = mem
        dockWidget.setWidget(mem)
        dockWidget.setWindowTitle("Memory-%d" % len(self.docks["memory"]))
        self.app.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dockWidget)

        titlebar = dockWidget.titleBarWidget()
        if isinstance(titlebar, DockTitleBar):
            titlebar.ui.btnClose.clicked.connect(lambda: self._close_dock(dockWidget, self.docks["memory"]))

            menu = titlebar.ui.btnMore.menu()
            action = self._addAction(menu, self.tr("Show in BinParser"), partial(self._openBinParserFromMemory, mem))
            # action.setIcon(QtGui.QIcon(":icon/images/ctrl/Memory_16x.svg"))
            menu.addSeparator()
            self._addAction(menu, self.tr("Dump Memory..."), mem.dumpBuffer)
            action = self._addAction(menu, self.tr("Add Memory View"), self.addMemoryView)
            action.setIcon(QtGui.QIcon(":icon/images/ctrl/Memory_16x.svg"))

        return dockWidget

    def _openBinParserFromMemory(self, mem: Memory):
        addr = mem.requestedAddress()
        size = mem.requestedSize()
        b = self.addBinParserView(addr, size)
        b.setWindowTitle("{:#08x} +{}".format(addr, size))

    def addBinParserView(self, addr: int, size: int) -> QtWidgets.QDockWidget:
        dockWidget = self.generate_dockwidget()
        # dockWidget.setWindowIcon(QtGui.QIcon(":icon/images/ctrl/Memory_16x.svg"))
        bp = BinParser(self.app)
        bp.viewAddress = addr
        bp.viewSize = size
        bp.loadFile(self._dbg.get_cached_stream(addr, size))
        self.docks["binparser"][dockWidget] = bp
        dockWidget.setWidget(bp)
        dockWidget.setWindowTitle("BinParser-%d" % len(self.docks["binparser"]))
        self.app.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dockWidget)

        titlebar = dockWidget.titleBarWidget()
        if isinstance(titlebar, DockTitleBar):
            titlebar.ui.btnClose.clicked.connect(lambda: self._close_dock(dockWidget, self.docks["binparser"]))

            menu = titlebar.ui.btnMore.menu()

            action = self._addAction(menu, self.tr("Stop All Auto Refresh Timers"), bp.var_watcher.clearAutoRefresh)
            action.setIcon(QtGui.QIcon(":icon/images/vswin2019/Timeout_16x.svg"))

            self._addAction(menu, self.tr("Export Parsing Result..."), bp.export_as_csv)

        return dockWidget
