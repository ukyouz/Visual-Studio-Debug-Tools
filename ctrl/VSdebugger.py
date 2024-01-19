import io
import sys
from dataclasses import dataclass
from dataclasses import field
from typing import Optional
from typing import Type

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import ClsType
from ctrl.qtapp import HistoryMenu
from ctrl.qtapp import Plugin
from ctrl.qtapp import PluginNotLoaded
from ctrl.qtapp import set_app_title
from ctrl.WidgetDockTitleBar import DockTitleBar
from ctrl.WidgetExpression import Expression
from ctrl.WidgetMemory import Memory
from ctrl.WidgetProcessSelector import ProcessSelector
from helper import qtmodel
from plugins import loadpdb
from view import VSdebugger
from view import resource


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
        ])

        editToolBar = QtWidgets.QToolBar("Process", self)
        editToolBar.setMovable(False)
        self.addToolBar(editToolBar)
        editToolBar.addWidget(ProcessSelector(self))

        self.dockWidget = self.generate_dockwidget()
        self.dockWidget.setWidget(Expression(self))
        self.dockWidget.setWindowTitle("Expression")
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.dockWidget)

        self.dockWidget2 = self.generate_dockwidget()
        self.dockWidget2.setWidget(Memory(self))
        self.dockWidget2.setWindowTitle("Memory")
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.dockWidget2)

    def generate_dockwidget(self):
        dockWidget = QtWidgets.QDockWidget(parent=self)
        dockWidget.setObjectName("dockWidget")
        dockWidget.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable
            |QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        dockWidget.setTitleBarWidget(DockTitleBar(dockWidget))
        dockWidget.setContentsMargins(0, 0, 0, 0)
        return dockWidget

    def loadPlugins(self, plugins: list[Plugin]):
        for p in plugins:
            self._plugins[p.__class__.__name__] = p
            p.setupMenues(self.ui.menubar)
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

    app = QtWidgets.QApplication(sys.argv)
    window = VisualStudioDebugger()
    window.show()
    sys.exit(app.exec())