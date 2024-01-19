import abc
from dataclasses import dataclass
from dataclasses import field
from functools import partial
from typing import Callable
from typing import NotRequired
from typing import Protocol
from typing import TypedDict
from typing import TypeVar

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from helper.qtthread import Runnable
from modules.utils.typ import DequeList


def set_app_title(app: QtWidgets.QMainWindow | QtWidgets.QWidget, title: str):
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

    def trigger(self, cmdname: str, **kwargs):
        self.cmds[cmdname](**kwargs)



ClsType = TypeVar("ClsType")


class UiForm(Protocol):
    def setupUi(self, MainWindow):
        ...

    def retranslateUi(self, MainWindow):
        ...


class AppCtrl(QtWidgets.QMainWindow):
    ui: UiForm

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.cmd = CommandManager()
        self.threadpool = QtCore.QThreadPool()
        self.app_setting = QtCore.QSettings("app.ini", QtCore.QSettings.Format.IniFormat)

    def run_cmd(self, cmdname, /, **kwargs):
        self.cmd.trigger(cmdname, **kwargs)

    def _print_error_thread(self, expt, tb):
        print(expt, tb)

    def exec_async(self, fn, *args, finished_cb=None, errored_cb=None, **kwargs):
        worker = Runnable(fn, *args, **kwargs)
        if finished_cb:
            worker.finished.connect(finished_cb)
        worker.errored.connect(self._print_error_thread)
        if errored_cb:
            worker.errored.connect(errored_cb)
        self.threadpool.start(worker)

    def loadPlugins(self, plugins: list):
        ...

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
    icon: NotRequired[str]
    submenus: NotRequired[list]


def normalized(name: str) -> str:
    name = name.replace("...", "")
    tbl = str.maketrans(" ", "_")
    return name.translate(tbl)


_translate = QtCore.QCoreApplication.translate


class PluginNotLoaded(Exception):
    """plugin not loaded"""


@dataclass
class Plugin:
    app: AppCtrl

    """ app usages """

    def setupMenues(self, parent):
        menues = self.registerMenues()

        def _make_menu(actions: list[MenuAction], menu: QtWidgets.QMenu):
            for act in actions:
                if act["name"] == "---":
                    menu.addSeparator()
                    continue
                if submenus := act.get("submenus", []):
                    submenu = self._addMenu(menu, act["name"])
                    _make_menu(submenus, submenu)
                    menu.addAction(submenu.menuAction())
                else:
                    action = self._makeAction(
                        self.app,
                        act["name"],
                        act.get("shortcut", None),
                        act.get("command", None),
                    )
                    if icon := act.get("icon", None):
                        action.setIcon(QtGui.QIcon(icon))
                    menu.addAction(action)

        _make_menu(menues, parent)

    def _addMenu(self, parent, name) -> QtWidgets.QMenu:
        norm_name = "menu" + normalized(name)
        menu = getattr(self.app.ui, norm_name, None)
        if menu is not None:
            menu.addSeparator()
        else:
            menu = QtWidgets.QMenu(parent=parent)
            menu.setObjectName(norm_name)
            menu.setTitle(_translate("MainWindow", name))
            setattr(self.app.ui, norm_name, menu)
        return menu

    def _makeAction(self, parent, name, shortcut=None, cmd=None):
        action = QtGui.QAction(parent=parent)
        norm_actname = "action" + normalized(name)
        action.setObjectName(norm_actname)
        action.setText(_translate("MainWindow", name))
        if shortcut:
            action.setShortcut(_translate("MainWindow", shortcut))
        if cmd:
            action.triggered.connect(partial(self.app.run_cmd, cmd))
        return action

    """ plugin usages """

    def menu(self, name) -> QtWidgets.QMenu:
        norm_name = "menu" + normalized(name)
        return getattr(self.app.ui, norm_name)

    def registerMenues(self) -> list[MenuAction]:
        return []

    def registerCommands(self) -> list[tuple]:
        return []

    def post_init(self):
        ...


class HistoryMenu(QtCore.QObject):
    actionTriggered = QtCore.pyqtSignal(object)

    def __init__(self, btn: QtWidgets.QToolButton) -> None:
        super().__init__()
        self.btn = btn
        self.data_list = DequeList()

    def _update_menu(self):
        menu = QtWidgets.QMenu()
        actgroup = QtGui.QActionGroup(menu)
        actgroup.setExclusive(True)
        def _add_action(menu, data):
            action = menu.addAction(title)
            action.setCheckable(True)
            action.triggered.connect(lambda: self.actionTriggered.emit(data))
            actgroup.addAction(action)

        for data in self.data_list:
            title = self.stringify(data)
            _add_action(menu, data)
        self.btn.setMenu(menu)

    def stringify(self, data) -> str:
        return ""

    def add_data(self, data):
        data_str = self.stringify(data)
        found_pos = -1
        for i, d in enumerate(self.data_list):
            if self.stringify(d) == data_str:
                found_pos = i
                break
        if found_pos >= 0:
            data = self.data_list.pop(found_pos)
        self.data_list.insert(0, data)
        self._update_menu()
