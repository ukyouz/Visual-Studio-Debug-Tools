import sys

from PyQt6 import QtCore
from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import set_app_title
from view import WidgetDockTitleBar


class DockTitleBar(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QDockWidget):
        super().__init__(parent)
        self.ui = WidgetDockTitleBar.Ui_Form()
        self.ui.setupUi(self)
        self.ui.btnMore.setContentsMargins(0, 0, 0, 0)
        self.ui.labelIcon.setVisible(False)
        self.ui.btnTimer.setDisabled(True)
        self.ui.btnTimer.setVisible(False)
        self.ui.btnTimer.clicked.connect(self._onBtnTimerClicked)
        self.app: AppCtrl = parent.parent()
        set_app_title(self, "")

        parent.installEventFilter(self)

        self.app.evt.add_hook("WidgetTimerStarted", self._setupTimerUI)
        self.app.evt.add_hook("WidgetTimerCleared", self._clearTimerUI)

    def eventFilter(self, obj: QtCore.QObject, e: QtCore.QEvent) -> bool:
        # ref: https://github.com/yjg30737/pyqt-custom-titlebar-window/blob/main/pyqt_custom_titlebar_window/customTitlebarWindow.py
        if isinstance(obj, QtWidgets.QDockWidget):
            match e.type():
                case QtCore.QEvent.Type.WindowTitleChange:
                    self.ui.labelTitle.setText(obj.windowTitle())
                case QtCore.QEvent.Type.WindowIconChange:
                    self.ui.labelIcon.setVisible(True)
                    icon = obj.windowIcon()
                    pixmap = icon.pixmap(icon.actualSize(self.ui.labelIcon.size()))
                    self.ui.labelIcon.setPixmap(pixmap)
        return False

    def _setupTimerUI(self, wid):
        w = self.parent().widget()
        if w != wid:
            return
        self.ui.btnTimer.setDisabled(False)
        self.ui.btnTimer.setVisible(True)
        self.ui.btnTimer.setChecked(True)

    def _clearTimerUI(self, wid):
        w = self.parent().widget()
        if w != wid:
            return
        self.ui.btnTimer.setDisabled(True)
        self.ui.btnTimer.setVisible(False)
        self.ui.btnTimer.setChecked(False)

    def _onBtnTimerClicked(self):
        on = self.ui.btnTimer.isChecked()
        w = self.parent().widget()
        if v := getattr(w, "var_watcher", None):
            if on:
                v.resumeAutoRefresh()
            else:
                v.pauseAutoRefresh()


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    window = DockTitleBar(None)
    window.show()
    sys.exit(app.exec())