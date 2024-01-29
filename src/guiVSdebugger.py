import sys
from collections import defaultdict
from typing import Type

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import ClsType
from ctrl.qtapp import MenuAction
from ctrl.qtapp import Plugin
from ctrl.qtapp import PluginNotLoaded
from ctrl.WidgetDockTitleBar import DockTitleBar
from ctrl.WidgetExpression import Expression
from ctrl.WidgetMemory import Memory
from ctrl.WidgetProcessSelector import ProcessSelector
from plugins import loadpdb
from view import VSdebugger
from view import resource


class Dock(Plugin):
    def registerMenues(self) -> list[MenuAction]:
        return [
            {
                "name": "Debugger",
                "submenus": [
                    {
                        "name": "Add Memory View",
                        "command": "AddMemoryView",
                        "icon": "view/images/ctrl/Memory_16x.svg",
                    },
                    {
                        "name": "Add Expression View",
                        "command": "AddExpressionView",
                        "icon": "view/images/ctrl/VariableExpression_16x.svg",
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
        self.app.tabifyDockWidget(de, dm)

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
        dockWidget.setWindowIcon(QtGui.QIcon("view/images/ctrl/VariableExpression_16x.svg"))
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
            action.setIcon(QtGui.QIcon("view/images/ctrl/Refresh_16x.svg"))
            self._addAction(menu, "Clear expressions", expr.clearTree)
            self._addAction(menu, "Add Expression View", self.addExpressionView)
            action.setIcon(QtGui.QIcon("view/images/ctrl/VariableExpression_16x.svg"))

        return dockWidget

    def addMemoryView(self):
        dockWidget = self.generate_dockwidget()
        dockWidget.setWindowIcon(QtGui.QIcon("view/images/ctrl/Memory_16x.svg"))
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
            action.setIcon(QtGui.QIcon("view/images/ctrl/Memory_16x.svg"))

        return dockWidget


class VisualStudioDebugger(AppCtrl):
    def __init__(self):
        super().__init__()
        self.ui = VSdebugger.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("VS Debugger")
        self.setWindowIcon(QtGui.QIcon("view/images/AnalysisServerConnection_16x.svg"))

        self._plugins = {}
        self.loadPlugins([
            loadpdb.LoadPdb(self),
            Dock(self),
        ])

        editToolBar = QtWidgets.QToolBar("Process", self)
        editToolBar.setMovable(False)
        processSelector = ProcessSelector(self)
        self.addToolBar(editToolBar)
        editToolBar.addWidget(processSelector)

        self.cmd.register("AttachCurrentProcess", processSelector.attach_current_selected_process)

    def loadPlugins(self, plugins: list[Plugin]):
        for p in plugins:
            self._plugins[p.__class__.__name__] = p
            self.setupMenues(self.ui.menubar, p.registerMenues())
            for cmdname, fn in p.registerCommands():
                self.cmd.register(cmdname, fn)
            p.post_init()

    def plugin(self, plg_cls: Type[ClsType]) -> ClsType:
        try:
            return self._plugins[plg_cls.__name__]
        except KeyError:
            raise PluginNotLoaded(plg_cls)


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    # https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7
    import ctypes
    myappid = __file__
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QtWidgets.QApplication(sys.argv)
    window = VisualStudioDebugger()
    window.show()
    sys.exit(app.exec())