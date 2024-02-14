import os
import sys
from datetime import datetime
from pathlib import Path
from pprint import pformat

from pyqode.core import api
from pyqode.core import modes
from pyqode.core import panels
from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import i18n
from ctrl.qtapp import set_app_title
from helper import qtmodel
from view import WidgetScript
from view import resource

tr = lambda txt: i18n("Script", txt)


class WidgetLogger:
    def __init__(self, editor) -> None:
        self.editor = editor

    def write(self, a):
        self.editor.printed.emit(a)

    def flush(self):
        ...


class Script(QtWidgets.QWidget):
    printed = QtCore.pyqtSignal(str)
    errored = QtCore.pyqtSignal(str)

    def __init__(self, app: AppCtrl):
        super().__init__()
        self.ui = WidgetScript.Ui_Form()
        self.ui.setupUi(self)
        set_app_title(self, "")
        self.setWindowIcon(QtGui.QIcon(":icon/images/vswin2019/FSScript_16x.svg"))

        self.app = app

        self._init_explorer()
        self._init_code_editor(self.ui.plaintextSource)

        self.ui.treeExplorer.doubleClicked.connect(self._onDoubleClickedExplorer)
        self.ui.btnLoadFile.clicked.connect(self._load_file)
        self.ui.btnSaveFile.clicked.connect(self._save_file)
        self.ui.btnRunScript.clicked.connect(self._run_script)
        self.ui.btnReset.clicked.connect(self._clear_screen)
        self.ui.plaintextSource.modificationChanged.connect(self._update_window_title)

        self.printed.connect(self._async_print_log)
        self.errored.connect(self._async_print_err)

        if file := self.app.app_setting.value("Script/scriptFile", None):
            self._load_file(file)
        if script := self.app.app_setting.value("Script/textSource", ""):
            self.ui.plaintextSource.setPlainText(script, "text/plain", "utf8")

        self.gui_stdout = WidgetLogger(self)

    def _init_explorer(self):
        model = qtmodel.FileExplorerModel(Path(""))
        flist = list((self.app.app_dir / "scripts").rglob("*.py"))
        model.addFiles(flist)
        self.ui.treeExplorer.setModel(model)
        self.ui.treeExplorer.setExpanded(model.index(0, 0), True)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        editor = self.ui.plaintextSource
        editor.backend.stop()
        self.app.app_setting.setValue("Script/textSource", self.ui.plaintextSource.toPlainText())
        if self.ui.plaintextSource.file.name:
            self.app.app_setting.setValue("Script/scriptFile", self.ui.labelFilename.text())

    def _init_code_editor(self, editor: api.CodeEdit):
        editor.backend.start("helper/pyqode_backend.py")
        editor.modes.append(modes.CodeCompletionMode())
        editor.modes.append(modes.PygmentsSyntaxHighlighter(editor.document()))
        editor.modes.get(modes.PygmentsSyntaxHighlighter).pygments_style = 'xcode'
        editor.modes.append(modes.CaretLineHighlighterMode())
        editor.modes.append(modes.AutoIndentMode())
        editor.modes.append(modes.CommentsMode())
        editor.modes.append(modes.SymbolMatcherMode())
        editor.modes.append(modes.OccurrencesHighlighterMode())
        editor.modes.append(modes.FileWatcherMode())
        editor.modes.get(modes.OccurrencesHighlighterMode).delay = 300
        # editor.modes.append(modes.OutlineMode())
        editor.panels.append(panels.SearchAndReplacePanel(), api.Panel.Position.BOTTOM)
        editor.panels.append(panels.LineNumberPanel(), api.Panel.Position.LEFT)
        editor.show_context_menu = True
        editor.action_indent.setShortcut("Ctrl+]")
        editor.action_un_indent.setShortcut("Ctrl+[")

    def _onDoubleClickedExplorer(self):
        indexes = self.ui.treeExplorer.selectedIndexes()
        model = self.ui.treeExplorer.model()
        if not isinstance(model, qtmodel.FileExplorerModel):
            return
        if len(indexes) == 1:
            item: Path = model.itemFromIndex(indexes[0])
            if item.is_file():
                self._load_file(str(item))

    def _update_window_title(self):
        editor = self.ui.plaintextSource
        filename = editor.file.name if editor.file.opening else ""
        set_app_title(self, filename)
        title = self.windowTitle()
        if filename and self.ui.plaintextSource.document().isModified():
            title = "(Modified) " + title
        self.setWindowTitle(title)

    def _load_file(self, filename: str=False):
        if self.ui.plaintextSource.document().isModified():
            rtn = QtWidgets.QMessageBox.warning(
                self,
                self.__class__.__name__,
                tr("Current script is not saved yet, do you want to overwrite it?"),
                QtWidgets.QMessageBox.StandardButton.Yes,
                QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if rtn == QtWidgets.QMessageBox.StandardButton.Cancel:
                return
        if not filename:
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                caption="Open File",
                directory=str(self.app.app_dir / "scripts"),
                filter="Any (*.py)"
            )
        if filename:
            if not os.path.exists(filename):
                QtWidgets.QMessageBox.warning(
                    self,
                    self.__class__.__name__,
                    tr("File not found: %r") % filename,
                )
                return
            self.ui.labelFilename.setText(filename)
            self.ui.plaintextSource.file.open(filename)

    def _save_file(self):
        filename = self.ui.labelFilename.text()
        if not os.path.exists(filename):
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                tr("Save new script to..."),
                directory=str(self.app.app_dir / "scripts"),
                filter="Any (*.py)",
            )
        if filename:
            self.ui.plaintextSource.file.save()
            self.ui.plaintextSource.document().setModified(False)
            self._init_explorer()

    def _clear_screen(self):
        self.ui.plaintextSource.file.close()
        self.ui.labelFilename.setText("")
        self.ui.labelRunningTime.setText("0:00:00")

    def _run_script(self):
        self.ui.plaintextLog.setPlainText("")

        script = self.ui.plaintextSource.toPlainText()
        start_time = datetime.now()

        def progressing():
            diff = datetime.now() - start_time
            delta_ts = str(diff)
            left, _ = delta_ts.split(".")
            self.ui.labelRunningTime.setText(left)

        timer = QtCore.QTimer()
        timer.timeout.connect(progressing)
        timer.start(1000)

        _backup = sys.stdout
        sys.stdout = self.gui_stdout

        def cb(_):
            timer.stop()
            self.ui.btnRunScript.setEnabled(True)
            self.ui.btnReset.setEnabled(True)
            sys.stdout = _backup

        self.ui.btnRunScript.setEnabled(False)
        self.ui.btnReset.setEnabled(False)
        self.app.exec_async(
            exec,
            script,
            {
                "app": self.app,
                # "print": lambda *a: self.printed.emit(" ".join(pformat(x) for x in a)),
            },
            errored_cb= lambda *a: self.errored.emit(" ".join(pformat(x) for x in a)),
            finished_cb=cb,
        )

    def _async_print_log(self, a: str):
        self.ui.plaintextLog.appendPlainText(a)

        # self.ui.plaintextLog.appendPlainText(a[:10000])
        # if len(a) > 10000:
        #     self.ui.plaintextLog.appendPlainText("...")

        # self.ui.plaintextLog.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        # self.ui.plaintextLog.insertPlainText(a)

    def _async_print_err(self, a: str):
        html_raw = a.replace("\n", "<br>")
        self.ui.plaintextLog.appendHtml("<span style='color: red'>%s</span>" % html_raw)


if __name__ == '__main__':
    from argparse import ArgumentParser

    from ctrl.qtapp import AppCtrl
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    window = Script(AppCtrl())
    window.show()
    sys.exit(app.exec())