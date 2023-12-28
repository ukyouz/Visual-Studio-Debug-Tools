import abc
from dataclasses import dataclass
from dataclasses import field
from functools import partial
from typing import Callable
from typing import NotRequired
from typing import TypedDict
from typing import TypeVar

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from helper.qtthread import Runnable


def set_app_title(app: QtWidgets.QMainWindow, title: str):
    clsname = app.__class__.__name__
    if title:
        app.setWindowTitle("%s - %s" % (title, clsname))
    else:
        app.setWindowTitle("%s" % title)


@dataclass
class CommandManager:
    cmds: dict[str, Callable] = field(default_factory=dict)

    def register(self, cmdname: str, fn: Callable):
        self.cmds[cmdname] = fn

    def trigger(self, cmdname: str):
        self.cmds[cmdname]()



ClsType = TypeVar("ClsType")


class AppCtrl(abc.ABC):
    view: QtWidgets.QMainWindow

    def __init__(self) -> None:
        self.cmd = CommandManager()
        self.threadpool = QtCore.QThreadPool()

    def run_cmd(self, cmdname):
        self.cmd.trigger(cmdname)

    def exec_async(self, fn, *args, finished_cb=None, errored_cb=None, **kwargs):
        worker = Runnable(fn, *args, **kwargs)
        if finished_cb:
            worker.finished.connect(finished_cb)
        if errored_cb:
            worker.errored.connect(errored_cb)
        self.threadpool.start(worker)

    @abc.abstractmethod
    def plugin(self, plugin_cls: ClsType) -> ClsType:
        """
        return the corresonding plugin instance

        Note:
            Why we leave implamatation to controller is
            because we need to construct plugins with parent set to ctrl itself.
            Ctrl can be anything, also we can NOT import any ctrl here
            or it will cause circular import error.
            You may want to raise some error when plugin is not loaded.
        """


class MenuAction(TypedDict):
    name: str
    command: NotRequired[str]
    shortcut: NotRequired[str]


def normalized(name: str) -> str:
    name = name.replace("...", "")
    tbl = str.maketrans(" ", "_")
    return name.translate(tbl)


_translate = QtCore.QCoreApplication.translate

@dataclass
class Plugin:
    ctrl: AppCtrl

    """ ctrl usages """

    def setupMenues(self, parent):
        menues = self.registerMenues()

        for name, actions in menues.items():
            menu = self._addMenu(parent, name)

            for act in actions:
                if act["name"] == "---":
                    menu.addSeparator()
                    continue
                action = self._makeAction(
                    self.ctrl.view,
                    act["name"],
                    act.get("shortcut", None),
                    act.get("command", None),
                )
                menu.addAction(action)
            parent.addAction(menu.menuAction())

    def _addMenu(self, parent, name) -> QtWidgets.QMenu:
        norm_name = "menu" + normalized(name)
        menu = getattr(self.ctrl, norm_name, None)
        if menu is not None:
            menu.addSeparator()
        else:
            menu = QtWidgets.QMenu(parent=parent)
            menu.setObjectName(norm_name)
            menu.setTitle(_translate("MainWindow", name))
            setattr(self.ctrl, norm_name, menu)
        return menu

    def _makeAction(self, parent, name, shortcut=None, cmd=None):
        action = QtGui.QAction(parent=parent)
        norm_actname = "action" + normalized(name)
        action.setObjectName(norm_actname)
        action.setText(_translate("MainWindow", name))
        if shortcut:
            action.setShortcut(_translate("MainWindow", shortcut))
        if cmd:
            action.triggered.connect(partial(self.ctrl.run_cmd, cmd))
        return action

    """ plugin usages """

    def menu(self, name) -> QtWidgets.QMenu:
        norm_name = "menu" + normalized(name)
        return getattr(self.ctrl, norm_name)

    def registerMenues(self) -> dict[str, list[MenuAction]]:
        return {}

    def registerCommands(self) -> list[tuple]:
        return []


