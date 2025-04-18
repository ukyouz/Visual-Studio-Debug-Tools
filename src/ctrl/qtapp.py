import abc
import logging
import math
from collections import defaultdict
from collections import deque
from contextlib import suppress
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


def clamp(minval, maxval, val):
    return max(minval, min(maxval, val))


def colorlarp(start: QtGui.QColor, end: QtGui.QColor, minval, maxval, val) -> QtGui.QColor:
    if minval > maxval:
        raise ValueError(f"{minval=} shall smaller than {maxval=}")
    _val = clamp(minval, maxval, val)
    _t = (_val - minval) / (maxval - minval)

    r = round(start.red() * _t + end.red() * (1 - _t))
    g = round(start.green() * _t + end.green() * (1 - _t))
    b = round(start.blue() * _t + end.blue() * (1 - _t))
    a = round(start.alpha() * _t + end.alpha() * (1 - _t))
    return QtGui.QColor.fromRgb(r, g, b, a)


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



@dataclass
class CommandManager:
    cmds: dict[str, Callable] = field(default_factory=dict)

    def register(self, cmdname: str, fn: Callable):
        self.cmds[cmdname] = fn

    def trigger(self, cmdname: str, **kwargs):
        self.cmds[cmdname](**kwargs)


@dataclass
class EventManager:
    evts: dict[str, deque[Callable]] = field(default_factory=partial(defaultdict, deque))

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

    def log(self, msg: str):
        logger.debug(msg)

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

        def _make_menu(actions: list[MenuAction], menu: QtWidgets.QMenu, ag: QtGui.QActionGroup | None=None):
            prev_pos = None
            for act in actions:
                if act["name"] == "---":
                    prev_action = _get_action_at(menu, prev_pos)
                    if prev_action:
                        menu.insertSeparator(prev_action)
                    else:
                        menu.addSeparator()
                    continue
                submenus = act.get("submenus", None)
                if isinstance(submenus, list):
                    submenu = self._addMenu(menu, act["name"])
                    ag = QtGui.QActionGroup(submenu) if act.get("actionGroup", False) else None
                    _make_menu(submenus, submenu, ag)
                    menu.addMenu(submenu)
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
            menu.setTitle(self.tr(name))
            setattr(self.ui, norm_name, menu)
        return menu

    def _makeAction(self, parent, name, shortcut=None, cmd=None):
        action = QtGui.QAction(parent=parent)
        norm_actname = "action" + normalized(name)
        assert not hasattr(self.ui, norm_actname), "Duplicated actioins"
        setattr(self.ui, norm_actname, action)
        action.setObjectName(norm_actname)
        action.setText(self.tr(name))
        if shortcut:
            action.setShortcut(shortcut)
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
class Plugin(QtCore.QObject):
    app: AppCtrl

    def __post_init__(self):
        super().__init__(self.app)

    def registerMenues(self) -> list[MenuAction]:
        return []

    def registerCommands(self) -> list[tuple]:
        return []

    def post_init(self):
        ...


class HistoryMenu(QtCore.QObject):
    actionTriggered = QtCore.pyqtSignal(object)
    cleared = QtCore.pyqtSignal()

    def __init__(self, menu: QtWidgets.QMenu, options: list=None, default=None) -> None:
        super().__init__()
        options = options or []
        self.menu = menu
        self.data_list = DequeList(options)
        self.recently_used_on_top = False
        self._current = default
        self._app_setting = (None, "")  # QtCore.QSettings, key
        self._redraw_menu()

    def _redraw_menu(self):
        self.menu.clear()
        actgroup = QtGui.QActionGroup(self.menu)
        actgroup.setExclusive(True)
        current = self.stringify(self._current) if self._current else None
        def _add_action(menu, _data):
            title = self.stringify(_data)
            action = menu.addAction(title)
            action.setCheckable(True)
            action.triggered.connect(lambda: self._selected(_data))
            action.triggered.connect(lambda: self.actionTriggered.emit(_data))
            if title == current:
                action.setChecked(True)
            actgroup.addAction(action)

        for data in self.data_list:
            _add_action(self.menu, data)

        if self.data_list:
            self.menu.addSeparator()
            action = self.menu.addAction(self.tr("Clear History"))
            action.triggered.connect(self._clear)

    def _selected(self, data):
        self._current = data
        if self.recently_used_on_top:
            self._redraw_menu()

    def _clear(self):
        self.menu.clear()
        self.data_list = DequeList()
        self._current = None
        self.cleared.emit()

    def stringify(self, data) -> str:
        return str(data)

    def add_data(self, data):
        data_str = self.stringify(data)
        found_pos = -1
        for i, d in enumerate(self.data_list):
            if self.stringify(d) == data_str:
                found_pos = i
                break
        need_pop_existance = self.recently_used_on_top and found_pos >= 0
        need_insert_front = self.recently_used_on_top or found_pos == -1

        if need_pop_existance:
            data = self.data_list.pop(found_pos)
        if need_insert_front:
            self.data_list.insert(0, data)

        if need_insert_front or self.stringify(self._current) != self.stringify(data):
            self._current = data
            self._redraw_menu()
            self._save_settings()

    def remove_data(self, data):
        self.data_list.remove(data)
        self._current = None
        self._redraw_menu()
        self._save_settings()

    def restore_from_settings(self, key: str, settings: QtCore.QSettings, *, auto_save=True):
        if auto_save:
            self._app_setting = (settings, key)
        if val := settings.value(key):
            self.data_list = DequeList(val)
            self._redraw_menu()

    def _save_settings(self):
        app_setting, key = self._app_setting
        if app_setting and key:
            app_setting.setValue(key, list(self.data_list))


class AutoRefreshTimer(QtCore.QObject):
    timeOut = QtCore.pyqtSignal(QtCore.QModelIndex)

    def __init__(self, parent, view: QtWidgets.QAbstractItemView):
        super().__init__(parent)
        self.view = view
        self.auto_refresh_timers = {}
        self.timer_indice = defaultdict(list)

    def onClosing(self):
        if self.auto_refresh_timers:
            rtn = QtWidgets.QMessageBox.warning(
                self.parent(),
                self.parent().__class__.__name__,
                self.tr("Auto refresh timers are still running, Ok to close?"),
                QtWidgets.QMessageBox.StandardButton.Ok,
                QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if rtn == QtWidgets.QMessageBox.StandardButton.Ok:
                self.clearAutoRefresh()
            return rtn
        else:
            return None

    def onDeleting(self):
        rtn = QtWidgets.QMessageBox.StandardButton.Yes
        if self.auto_refresh_timers:
            rtn = QtWidgets.QMessageBox.warning(
                self.parent(),
                self.parent().__class__.__name__,
                self.tr("Deleting any item stops all the auto refresh timers, is that OK?"),
                QtWidgets.QMessageBox.StandardButton.Ok,
                QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if rtn == QtWidgets.QMessageBox.StandardButton.Ok:
                self.clearAutoRefresh()
        return rtn

    def onAnyRelatedOperating(self):
        rtn = QtWidgets.QMessageBox.StandardButton.Yes
        if self.auto_refresh_timers:
            rtn = QtWidgets.QMessageBox.warning(
                self.parent(),
                self.parent().__class__.__name__,
                self.tr("You need to stop all the auto refresh timers to continue, is that OK?"),
                QtWidgets.QMessageBox.StandardButton.Ok,
                QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if rtn == QtWidgets.QMessageBox.StandardButton.Ok:
                self.clearAutoRefresh()
        return rtn

    def createContextMenues(self, indexes: list[QtCore.QModelIndex]):
        submenu = QtWidgets.QMenu(self.tr("Refresh Timer"))
        submenu.setIcon(QtGui.QIcon(":icon/images/vswin2019/Time_color_16x.svg"))
        actions = {
            500: submenu.addAction(self.tr("0.5 Second"), lambda: self._add_auto_refresh_index(indexes, 500)),
            1000: submenu.addAction(self.tr("1 Second"), lambda: self._add_auto_refresh_index(indexes, 1000)),
            2000: submenu.addAction(self.tr("2 Seconds"), lambda: self._add_auto_refresh_index(indexes, 2000)),
            5000: submenu.addAction(self.tr("5 Seconds"), lambda: self._add_auto_refresh_index(indexes, 5000)),
        }
        submenu.addSeparator()
        submenu.addAction(self.tr("Custom Time Interval..."), lambda: self._add_auto_refresh_index(indexes, None))
        customized = set()
        for i in indexes:
            if t := self.auto_refresh_timers.get(i, None):
                if act := actions.get(t.interval(), None):
                    act.setCheckable(True)
                    act.setChecked(True)
                else:
                    customized.add(t.interval())
        for time in customized:
            act = submenu.addAction("%d ms" % time, lambda: self._add_auto_refresh_index(indexes, time))
            act.setCheckable(True)
            act.setChecked(True)
        if any(i in self.auto_refresh_timers for i in indexes):
            submenu.addSeparator()
            plural = "s" if len(indexes) > 1 else ""
            act = submenu.addAction(self.tr("Stop Selected Timer{p}").format(p=plural), lambda: self.clearAutoRefresh(indexes))
            act.setIcon(QtGui.QIcon(":icon/images/vswin2019/Timeout_16x.svg"))
        return submenu

    def _add_auto_refresh_index(self, indexes: list[QtCore.QModelIndex], timeout: int | None):
        if timeout is None:
            timeout, ok = QtWidgets.QInputDialog.getInt(
                self.parent(),
                self.parent().__class__.__name__,
                self.tr("Set an interval (unit: ms)"),
                min=100,
                step=100,
            )
            if not ok:
                return
        if len(indexes) == 0:
            return

        def _timeout(indexes):
            for i in indexes:
                model = self.view.model()
                model.dataChanged.emit(i, i, [QtCore.Qt.ItemDataRole.UserRole])
                self.timeOut.emit(i)

        model = self.view.model()
        timer = QtCore.QTimer()
        color = colorlarp(QtGui.QColor("#f1fbd7"), QtGui.QColor("#ffe000"), math.log(500), math.log(10000), math.log(timeout))
        for i in indexes:
            model.setData(i, QtGui.QColor(color), QtCore.Qt.ItemDataRole.BackgroundRole)

            prev_timer = self.auto_refresh_timers.get(i, None)
            if prev_timer is not None:
                indice = self.timer_indice.get(prev_timer, [])
                if indice:
                    with suppress(ValueError):
                        indice.remove(i)
                    if not indice:
                        prev_timer.stop()
                        del self.timer_indice[prev_timer]

            self.auto_refresh_timers[i] = timer

        timer.timeout.connect(partial(_timeout, indexes))
        self.timer_indice[timer] = indexes
        timer.setInterval(timeout)
        timer.start()

        self.parent().app.evt.apply_hook("WidgetTimerStarted", self.parent())

    def resumeAutoRefresh(self):
        for timer in self.timer_indice.keys():
            timer.start()

        model = self.view.model()
        for i, timer in self.auto_refresh_timers.items():
            timeout = timer.interval()
            color = colorlarp(QtGui.QColor("#f1fbd7"), QtGui.QColor("#ffe000"), math.log(500), math.log(10000), math.log(timeout))
            model.setData(i, QtGui.QColor(color), QtCore.Qt.ItemDataRole.BackgroundRole)
            br = model.index(i.row(), model.columnCount() - 1, i.parent())
            model.dataChanged.emit(i, br, [QtCore.Qt.ItemDataRole.BackgroundRole])

    def pauseAutoRefresh(self):
        for timer in self.timer_indice.keys():
            timer.stop()

        model = self.view.model()
        for i, timer in self.auto_refresh_timers.items():
            timeout = timer.interval()
            color = colorlarp(QtGui.QColor("#d3dac2"), QtGui.QColor("#d2c669"), math.log(500), math.log(10000), math.log(timeout))
            model.setData(i, QtGui.QColor(color), QtCore.Qt.ItemDataRole.BackgroundRole)
            br = model.index(i.row(), model.columnCount() - 1, i.parent())
            model.dataChanged.emit(i, br, [QtCore.Qt.ItemDataRole.BackgroundRole])

    def clearAutoRefresh(self, indexes: list[QtCore.QModelIndex]=None) -> int:
        model = self.view.model()
        indexes = indexes or list(self.auto_refresh_timers.keys())
        for i in indexes:
            if timer := self.auto_refresh_timers.get(i):
                model.setData(i, None, QtCore.Qt.ItemDataRole.BackgroundRole)
                model.dataChanged.emit(i, i, [QtCore.Qt.ItemDataRole.UserRole])
                timer.stop()

                indice = self.timer_indice[timer]
                assert indice != []
                indice.remove(i)
                if indice == []:
                    del self.timer_indice[timer]

                del self.auto_refresh_timers[i]
        if not self.auto_refresh_timers:
            self.parent().app.evt.apply_hook("WidgetTimerCleared", self.parent())
        return len(indexes)