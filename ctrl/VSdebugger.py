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
from ctrl.qtapp import PluginNotLoaded
from ctrl.qtapp import set_app_title
from ctrl.WidgetExpression import CtrlExpression
from ctrl.WidgetProcessSelector import CtrlProcessSelector
from helper import qtmodel
from plugins import loadpdb
from view import VSdebugger
from view import resource


class VisualStudioDebugger(AppCtrl, VSdebugger.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.view = QtWidgets.QMainWindow()
        self.setupUi(self.view)
        set_app_title(self.view, "")

        self.app_setting = QtCore.QSettings("app.ini", QtCore.QSettings.Format.IniFormat)

        self.dockWidget = self.generate_dockwidget()
        self.dockWidget.setWidget(CtrlExpression(self).view)
        self.dockWidget.resize(self.view.size())
        self.view.addDockWidget(QtCore.Qt.DockWidgetArea.TopDockWidgetArea, self.dockWidget)

        self.dockWidget2 = self.generate_dockwidget()
        self.dockWidget2.setWidget(CtrlExpression(self).view)
        self.dockWidget2.resize(self.view.size())
        self.view.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, self.dockWidget2)

        editToolBar = QtWidgets.QToolBar("Edit", self.view)
        editToolBar.setMovable(False)
        self.view.addToolBar(editToolBar)
        # self.process_ctrl = CtrlProcessSelector(self)
        editToolBar.addWidget(CtrlProcessSelector(self).view)

        self._plugins = {}
        self.loadPlugins([
            loadpdb.LoadPdb(self),
        ])

    def generate_dockwidget(self):
        dockWidget = QtWidgets.QDockWidget(parent=self.view)
        dockWidget.setObjectName("dockWidget")
        dockWidget.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable
            |QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        return dockWidget

    def loadPlugins(self, plugins: list[Plugin]):
        for p in plugins:
            self._plugins[p.__class__.__name__] = p
            p.setupMenues(self.menubar)
            for cmdname, fn in p.registerCommands():
                self.cmd.register(cmdname, fn)

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
    window.view.show()
    sys.exit(app.exec())