import logging
import sys
from pathlib import Path

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import set_app_title
from helper import qtmodel
from modules.pdbparser.pdbparser import picklepdb
from view import WidgetPicklePdb
from view import resource


class PicklePdb(QtWidgets.QWidget):
    loaded = QtCore.pyqtSignal(str)

    def __init__(self, app: AppCtrl):
        super().__init__()
        self.ui = WidgetPicklePdb.Ui_Form()
        self.ui.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(":icon/images/vswin2019/Database_16x.svg"))
        set_app_title(self, "")

        self.app = app
        self.ui.btnOpenFolder.clicked.connect(self._open_folder)
        self.ui.btnGenerateSelected.clicked.connect(self._generate_pdbin)
        self.ui.btnLoadSelected.clicked.connect(self._load_pdbin)

        if app and (val := self.app.app_setting.value("LoadPdb/pdbin", "")):
            self.setEnabled(False)
            loaded_db_folder = Path(val).parent.parent  # TARGET/vsdbg/xx.pdbin
            QtCore.QTimer.singleShot(0, lambda: self._open_folder(loaded_db_folder))

    def _open_folder(self, folder=""):
        if not folder:
            if self.app:
                prev_folder = self.app.app_setting.value("LoadPdb/lastGeneratedFolder", "")
            else:
                prev_folder = ""
            folder = QtWidgets.QFileDialog.getExistingDirectory(
                self,
                directory=prev_folder,
                caption="Open VS build folder",
            )
        if not folder:
            return

        root = Path(folder)
        model = qtmodel.FileExplorerModel(Path())
        model.showFullpathRoot = False
        model.addFolder(root)
        model.addFiles(list(root.rglob("*.pdb")))
        self.ui.treePdb.setModel(model)
        if model.rowCount():
            self.ui.treePdb.setExpanded(model.index(0, 0), True)

        self.ui.labelFolder.setText(str(root))
        self._on_generated_done()
        self.setEnabled(True)

    def _generate_pdbin(self):
        indexes = [x for x in self.ui.treePdb.selectedIndexes() if x.column() == 0]
        model = self.ui.treePdb.model()
        if indexes and isinstance(model, qtmodel.FileExplorerModel):
            files = [model.itemFromIndex(x) for x in indexes]
            logging.info("Generate: %r" % [model.itemFromIndex(x) for x in indexes])

            def progressing():
                val = self.ui.progressBar.value()
                self.ui.progressBar.setValue(val + 1)

            timer = QtCore.QTimer()
            timer.timeout.connect(progressing)
            timer.start(1000)

            self.ui.progressBar.setMaximum(200)
            def cb(res):
                timer.stop()
                self.ui.progressBar.setValue(200)
                if res is None:
                    return
                QtWidgets.QMessageBox.information(
                    self,
                    self.__class__.__name__,
                    "Generation Done!",
                )
                self._on_generated_done()

            def err(e, tb):
                self.ui.progressBar.setStyleSheet("QProgressBar::chunk {background: red}")
                QtWidgets.QMessageBox.warning(
                    self,
                    self.__class__.__name__,
                    tb + str(e),
                )

            self.ui.progressBar.setValue(0)
            self.ui.progressBar.setPalette(self.palette())
            self.ui.progressBar.setStyleSheet("")
            self.app.exec_async(
                picklepdb.convert_pdbs,
                pdb_files = files,
                out_dir = Path(self.ui.labelFolder.text()) / ".vsdbg",
                finished_cb=cb,
                errored_cb=err,
                block_UIs=[
                    self.ui.treePdb,
                    self.ui.btnGenerateSelected,
                ],
            )

    def _on_generated_done(self):
        root = Path(self.ui.labelFolder.text())
        model = qtmodel.FileExplorerModel(Path())
        model.showFullpathRoot = False
        model.addFiles(list(root.rglob("*.pdbin")))
        self.ui.treeBin.setModel(model)
        if model.rowCount():
            self.ui.treeBin.setExpanded(model.index(0, 0), True)

        if self.app:
            self.app.app_setting.setValue("LoadPdb/lastGeneratedFolder", str(root))

    def _load_pdbin(self):
        model = self.ui.treeBin.model()
        if not isinstance(model, qtmodel.FileExplorerModel):
            QtWidgets.QMessageBox.warning(
                self,
                self.__class__.__name__,
                "Generate one from .pdb then try again.",
            )
            return
        indexes = [x for x in self.ui.treeBin.selectedIndexes() if x.column() == 0]
        if len(indexes) == 0:
            QtWidgets.QMessageBox.warning(
                self,
                self.__class__.__name__,
                "Select one .pdbin file and press [Load].",
            )
            return
        file = model.itemFromIndex(indexes[0])
        self.loaded.emit(str(file))
        self.close()


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()

    app = QtWidgets.QApplication(sys.argv)
    window = PicklePdb(None)
    window.show()
    sys.exit(app.exec())