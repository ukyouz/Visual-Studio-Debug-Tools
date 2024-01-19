import io
import sys

from PyQt6 import QtWidgets

from ctrl.BinView import BinViewer


class BinViewerApp(BinViewer):
    def __init__(self, fileio=None):
        super().__init__(fileio)


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("file", nargs="?", default="")
    args = p.parse_args()

    app = QtWidgets.QApplication(sys.argv)

    fileio = None
    if args.file:
        with open(args.file, "rb") as fs:
            fileio = io.BytesIO(fs.read())
    window = BinViewerApp(fileio)
    window.show()
    sys.exit(app.exec())
