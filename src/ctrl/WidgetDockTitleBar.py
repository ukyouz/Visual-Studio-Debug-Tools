import sys

from PyQt6 import QtCore
from PyQt6 import QtWidgets

from ctrl.qtapp import set_app_title
from view import WidgetDockTitleBar


class DockTitleBar(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QDockWidget):
        super().__init__(parent)
        self.ui = WidgetDockTitleBar.Ui_Form()
        self.ui.setupUi(self)
        self.ui.btnMore.setContentsMargins(0, 0, 0, 0)
        self.ui.labelIcon.setVisible(False)
        set_app_title(self, "")

        parent.installEventFilter(self)

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



if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    window = DockTitleBar(None)
    window.show()
    sys.exit(app.exec())