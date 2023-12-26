import io
import sys
from PyQt6 import QtWidgets

from views import MyQt
from views.ui import BinView


def set_app_title(app: QtWidgets.QMainWindow, filename: str):
    clsname = app.__class__.__name__
    if filename:
        app.setWindowTitle("%s - %s" % (filename, clsname))
    else:
        app.setWindowTitle("%s" % filename)


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
        self.ui.actionLoad_PDB_file.triggered.connect(self._onPdbinLoad)
        self.ui.btnParse.clicked.connect(self._onBtnParseClicked)
        self.ui.lineStruct.returnPressed.connect(self._onBtnParseClicked)
        self.ui.lineOffset.returnPressed.connect(self._onBtnParseClicked)

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
        model = MyQt.HexTable(self.ui.tableView, fileio)
        self.ui.tableView.setModel(model)

    def _onBtnParseClicked(self):
        print(self.ui.lineStruct.text())
        print(self.ui.lineOffset.text())


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