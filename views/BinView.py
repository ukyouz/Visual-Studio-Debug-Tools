import io
import sys
from dataclasses import dataclass
from dataclasses import field
from functools import partial
from typing import Callable
from typing import NotRequired
from typing import TypedDict

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from views import qtmodel
from views.ui import BinView


def set_app_title(app: QtWidgets.QMainWindow, filename: str):
    clsname = app.__class__.__name__
    if filename:
        app.setWindowTitle("%s - %s" % (filename, clsname))
    else:
        app.setWindowTitle("%s" % filename)


@dataclass
class CommandManager:
    cmds: dict[str, Callable] = field(default_factory=dict)

    def register(self, cmdname: str, fn: Callable):
        self.cmds[cmdname] = fn

    def trigger(self, cmdname: str):
        self.cmds[cmdname]()


class BinViewer(QtWidgets.QMainWindow):
    def __init__(self, fileio=None):
        super().__init__()
        self.ui = BinView.Ui_MainWindow()
        self.ui.setupUi(self)
        set_app_title(self, "")

        # properties
        self.fileio = fileio
        if fileio:
            self._loadFile(fileio)

        # events
        self.ui.actionOpen_File.triggered.connect(self._onFileOpened)
        self.ui.btnParse.clicked.connect(self._onBtnParseClicked)
        self.ui.lineStruct.returnPressed.connect(self._onBtnParseClicked)
        self.ui.lineOffset.returnPressed.connect(self._onBtnParseClicked)

        # plugins pool
        self.cmd = CommandManager()
        self.plugins = [
            LoadPdb(self),
        ]
        for p in self.plugins:
            p.setupMenues(self.ui.menubar)
            for cmdname, fn in p.registerCommands():
                self.cmd.register(cmdname, fn)

    def run_cmd(self, cmdname):
        self.cmd.trigger(cmdname)

    def _onFileOpened(self, filename=False):
        if not filename:
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                caption="Open File",
                filter="Any (*.*)"
            )
        if filename:
            with open(filename, "rb") as fs:
                self.fileio = io.BytesIO(fs.read())
                self.fileio.name = filename
                self._loadFile(self.fileio)

    def _loadFile(self, fileio: io.IOBase):
        set_app_title(self, getattr(fileio, "name", "noname"))
        model = qtmodel.HexTable(self.ui.tableView, fileio)
        self.ui.tableView.setModel(model)

    def _onBtnParseClicked(self):
        print(self.ui.lineStruct.text())
        print(self.ui.lineOffset.text())


def normalized(name: str) -> str:
    name = name.replace("...", "")
    tbl = str.maketrans(" ", "_")
    return name.translate(tbl)


class MenuAction(TypedDict):
    name: str
    command: NotRequired[str]
    shortcut: NotRequired[str]


@dataclass
class Plugin:
    ctrl: BinViewer

    def setupMenues(self, parent):
        _translate = QtCore.QCoreApplication.translate

        menues = self.registerMenues()

        for name, actions in menues.items():
            menu = getattr(self.ctrl.ui, "menu" + name, None)
            if menu is not None:
                menu.addSeparator()
            else:
                menu = QtWidgets.QMenu(parent=parent)
                norm_name = normalized(name)
                menu.setObjectName("menu" + norm_name)
                menu.setTitle(_translate("MainWindow", name))
                setattr(self.ctrl.ui, norm_name, menu)

            for act in actions:
                if act["name"] == "---":
                    menu.addSeparator()
                    continue
                action = QtGui.QAction(parent=self.ctrl)
                norm_actname = normalized(act["name"])
                action.setObjectName("action" + norm_actname)
                action.setText(_translate("MainWindow", act["name"]))
                if "shortcut" in act:
                    action.setShortcut(_translate("MainWindow", act["shortcut"]))
                if "command" in act:
                    action.triggered.connect(partial(self.ctrl.run_cmd, act["command"]))
                menu.addAction(action)
            parent.addAction(menu.menuAction())

    def registerMenues(self) -> dict[str, list[MenuAction]]:
        return {}

    def registerCommands(self) -> list[tuple]:
        return []


class LoadPdb(Plugin):

    def registerMenues(self) -> dict[str, list[MenuAction]]:
        return {
            "PDB": [
                {
                    "name": "Load PDB file...",
                    "command": "LoadPdbin",
                    # "shortcut": "",
                },
            ]
        }

    def registerCommands(self):
        return [
            ("LoadPdbin", self._open_pdbin),
        ]

    def _open_pdbin(self):
        print(123)


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("--file", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)

    fileio = io.BytesIO()
    if args.file:
        with open(args.file, "rb") as fs:
            fileio = io.BytesIO(fs.read())
    window = BinViewer(fileio)
    window.show()
    sys.exit(app.exec())