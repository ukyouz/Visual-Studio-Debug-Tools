from collections import defaultdict

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from ctrl.qtapp import MenuAction
from ctrl.qtapp import Plugin
from ctrl.WidgetDockTitleBar import DockTitleBar
from ctrl.WidgetExpression import Expression
from ctrl.WidgetMemory import Memory


class Dock(Plugin):
    def registerMenues(self) -> list[MenuAction]:
        return [
            {
                "name": "Debugger",
                "submenus": [
                    {
                        "name": "Add Memory View",
                        "command": "AddMemoryView",
                        "icon": ":icon/images/ctrl/Memory_16x.svg",
                    },
                    {
                        "name": "Add Expression View",
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

        # initialize dock widgets
        de = self.addExpressionView()
        dm = self.addMemoryView()

        width = self.app.size().width()
        self.app.resizeDocks([dm], [width * 2 // 3], QtCore.Qt.Orientation.Horizontal)
        self.app.tabifyDockWidget(dm, de)

    def generate_dockwidget(self):
        dockWidget = QtWidgets.QDockWidget(parent=self.app)
        dockWidget.setObjectName("dockWidget")
        dockWidget.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable
            |QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        titelbar = DockTitleBar(dockWidget)
        dockWidget.setTitleBarWidget(titelbar)
        dockWidget.setContentsMargins(0, 0, 0, 0)
        menu = QtWidgets.QMenu()
        titelbar.ui.btnMore.setMenu(menu)
        return dockWidget

    def _addAction(self, menu, title, cb):
        action = menu.addAction(title)
        action.triggered.connect(cb)
        return action

    def _close_dock(self, dockWidget, widget_dict: dict):
        self.app.removeDockWidget(dockWidget)
        del widget_dict[dockWidget]

    def addExpressionView(self):
        dockWidget = self.generate_dockwidget()
        dockWidget.setWindowIcon(QtGui.QIcon(":icon/images/ctrl/VariableExpression_16x.svg"))
        expr = Expression(self.app)
        self.docks["expression"][dockWidget] = expr
        dockWidget.setWidget(expr)
        dockWidget.setWindowTitle("Expression-%d" % len(self.docks["expression"]))
        self.app.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dockWidget)

        titlebar = dockWidget.titleBarWidget()
        if isinstance(titlebar, DockTitleBar):
            menu = titlebar.ui.btnMore.menu()
            self._addAction(menu, "Close", lambda: self._close_dock(dockWidget, self.docks["expression"]))
            menu.addSeparator()
            action = self._addAction(menu, "Refresh", expr.refreshTree)
            action.setIcon(QtGui.QIcon(":icon/images/ctrl/Refresh_16x.svg"))
            self._addAction(menu, "Clear expressions", expr.clearTree)
            action = self._addAction(menu, "Add Expression View", self.addExpressionView)
            action.setIcon(QtGui.QIcon(":icon/images/ctrl/VariableExpression_16x.svg"))

        return dockWidget

    def addMemoryView(self):
        dockWidget = self.generate_dockwidget()
        dockWidget.setWindowIcon(QtGui.QIcon(":icon/images/ctrl/Memory_16x.svg"))
        mem = Memory(self.app)
        self.docks["memory"][dockWidget] = mem
        dockWidget.setWidget(mem)
        dockWidget.setWindowTitle("Memory-%d" % len(self.docks["memory"]))
        self.app.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dockWidget)

        titlebar = dockWidget.titleBarWidget()
        if isinstance(titlebar, DockTitleBar):
            menu = titlebar.ui.btnMore.menu()
            self._addAction(menu, "Close", lambda: self._close_dock(dockWidget, self.docks["memory"]))
            menu.addSeparator()
            self._addAction(menu, "Dump Memory...", mem.dumpBuffer)
            action = self._addAction(menu, "Add Memory View", self.addMemoryView)
            action.setIcon(QtGui.QIcon(":icon/images/ctrl/Memory_16x.svg"))

        return dockWidget
