import io
import sys

from PyQt6 import QtWidgets

from ctrl.BinView import BinViewer
# for pickle to work
from modules.pdbparser.parser import PDB7
from modules.pdbparser.parser import DbiStream
from modules.pdbparser.parser import OldDirectory
from modules.pdbparser.parser import PdbStream
from modules.pdbparser.parser import Stream
from modules.pdbparser.parser import TpiStream
from plugins.loadpdb import LoadPdb


class BinViewerApp(BinViewer):
    def __init__(self, fileio=None):
        super().__init__(fileio)


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
    window = BinViewerApp(fileio)
    window.view.show()
    sys.exit(app.exec())
