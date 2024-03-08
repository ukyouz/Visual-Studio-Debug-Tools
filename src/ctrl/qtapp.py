import abc
import logging
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
from functools import partial
from pathlib import Path
from typing import Callable
from typing import NotRequired
from typing import Protocol
from typing import Self
from typing import Type
from typing import TypedDict
from typing import TypeVar

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from helper.qtthread import Runnable
from modules.utils.typ import DequeList


class LogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.name.startswith("pyqode."):
            return False
        return True


logging.basicConfig(
    format="[%(asctime)s][%(name)-5s][%(levelname)-5s] %(message)s (%(filename)s:%(lineno)d)",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
)
logging.getLogger().handlers[0].addFilter(LogFilter(__name__))
logger = logging.getLogger(__name__)


def set_app_title(app: QtWidgets.QMainWindow | QtWidgets.QWidget, title: str):
    clsname = app.__class__.__name__
    if title:
        app.setWindowTitle("%s - %s" % (title, clsname))
    else:
        app.setWindowTitle("%s" % clsname)


i18n = QtCore.QCoreApplication.translate


@dataclass
class CommandManager:
    cmds: dict[str, Callable] = field(default_factory=dict)

    def register(self, cmdname: str, fn: Callable):
        self.cmds[cmdname] = fn

    def trigger(self, cmdname: str, **kwargs):
        self.cmds[cmdname](**kwargs)


@dataclass
class EventManager:
    evts: dict[str, list[Callable]] = field(default_factory=partial(defaultdict, list))

    def apply_hook(self, eventname: str, *args, **kwargs):
        for fn in self.evts.get(eventname, []):
            fn(*args, **kwargs)

    def add_hook(self, eventname: str, fn: Callable):
        if fn not in self.evts.get(eventname, []):
            self.evts[eventname].append(fn)


ClsType = TypeVar("ClsType")


class UiForm(Protocol):
    def setupUi(self, MainWindow):
        ...

    def retranslateUi(self, MainWindow):
        ...


class AppCtrl(QtWidgets.QMainWindow):
    ui: UiForm
    app_dir: Path = Path(".")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.cmd = CommandManager()
        self.evt = EventManager()
        self.threadpool = QtCore.QThreadPool()
        self.app_setting = QtCore.QSettings("app.ini", QtCore.QSettings.Format.IniFormat)

    def run_cmd(self, cmdname, /, **kwargs):
        self.cmd.trigger(cmdname, **kwargs)

    def _print_error_thread(self, expt, tb):
        logger.error(tb)

    def exec_async(self, fn, *args, finished_cb=None, errored_cb=None, block_UIs=None, **kwargs):
        block_UIs = block_UIs or []
        for ui in block_UIs:
            ui.setEnabled(False)
        def _enable_ui(*_):
            for ui in block_UIs:
                ui.setEnabled(True)

        worker = Runnable(fn, *args, **kwargs)
        if finished_cb:
            worker.finished.connect(finished_cb)
        worker.finished.connect(_enable_ui)
        worker.errored.connect(self._print_error_thread)
        if errored_cb:
            worker.errored.connect(errored_cb)
        self.threadpool.start(worker)

    def loadPlugins(self, plugins: list):
        ...

    @abc.abstractmethod
    def plugin(self, plugin_cls: Type[ClsType]) -> ClsType:
        """
        return the corresonding plugin instance

        Note:
            Why we leave implamatation to controller is
            because we need to construct plugins with parent set to ctrl itself.
            Ctrl can be anything, also we can NOT import any ctrl here
            or it will cause circular import error.
            You may want to raise some error when plugin is not loaded.
        """

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.evt.apply_hook("ApplicationClosed", a0)

    def menu(self, name) -> QtWidgets.QMenu:
        norm_name = "menu" + normalized(name)
        return getattr(self.ui, norm_name)

    def action(self, name) -> QtGui.QAction:
        norm_name = "action" + normalized(name)
        return getattr(self.ui, norm_name)

    def setupMenues(self, parent, menues):

        def _get_action_at(menu, pos):
            if pos is None:
                return None
            childs = menu.actions()
            try:
                return childs[pos]
            except IndexError:
                return None

        def _make_menu(actions: list[MenuAction], menu: QtWidgets.QMenu, ag: QtGui.QActionGroup=None):
            prev_pos = None
            for act in actions:
                if act["name"] == "---":
                    prev_action = _get_action_at(menu, prev_pos)
                    if prev_action:
                        menu.insertSeparator(prev_action)
                    else:
                        menu.addSeparator()
                    continue
                if submenus := act.get("submenus", []):
                    submenu = self._addMenu(menu, i18n("MainWindow", act["name"]))
                    ag = QtGui.QActionGroup(submenu) if act.get("actionGroup", False) else None
                    _make_menu(submenus, submenu, ag)
                    menu.addAction(submenu.menuAction())
                else:
                    action = self._makeAction(
                        self,
                        act["name"],
                        act.get("shortcut", None),
                        act.get("command", None),
                    )
                    if icon := act.get("icon", None):
                        action.setIcon(QtGui.QIcon(icon))
                    if ag:
                        ag.addAction(action)
                        action.setCheckable(True)
                    if check := act.get("checked", False):
                        action.setChecked(check)
                    prev_action = None
                    pos = act.get("position", prev_pos)
                    if pos is not None:
                        prev_pos = pos + 1
                        prev_action = _get_action_at(menu, pos)
                    if prev_action:
                        menu.insertAction(prev_action, action)
                    else:
                        menu.addAction(action)

        _make_menu(menues, parent)

    def _addMenu(self, parent, name) -> QtWidgets.QMenu:
        norm_name = "menu" + normalized(name)
        menu = getattr(self.ui, norm_name, None)
        if menu is not None:
            menu.addSeparator()
        else:
            menu = QtWidgets.QMenu(parent=parent)
            menu.setObjectName(norm_name)
            menu.setTitle(i18n("MainWindow", name))
            setattr(self.ui, norm_name, menu)
        return menu

    def _makeAction(self, parent, name, shortcut=None, cmd=None):
        action = QtGui.QAction(parent=parent)
        norm_actname = "action" + normalized(name)
        assert not hasattr(self.ui, norm_actname), "Duplicated actioins"
        setattr(self.ui, norm_actname, action)
        action.setObjectName(norm_actname)
        action.setText(i18n("MainWindow", name))
        if shortcut:
            action.setShortcut(i18n("MainWindow", shortcut))
        if cmd:
            action.triggered.connect(partial(self.run_cmd, cmd))
        return action

class MenuAction(TypedDict):
    name: str
    command: NotRequired[str]
    shortcut: NotRequired[str]
    icon: NotRequired[str]
    position: NotRequired[int]
    submenus: NotRequired[list[Self]]
    checked: NotRequired[bool]
    actionGroup: NotRequired[bool]


def normalized(name: str) -> str:
    name = name.replace("...", "")
    tbl = str.maketrans(" ", "_")
    return name.translate(tbl)


class PluginNotLoaded(Exception):
    """plugin not loaded"""


@dataclass
class Plugin:
    app: AppCtrl

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

        menu.addSeparator()
        action = menu.addAction("Clear History")
        action.triggered.connect(lambda: self.btn.menu().clear())

        self.btn.setMenu(menu)

    def stringify(self, data) -> str:
        return str(data)

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
