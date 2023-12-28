import io
import math
import os

from PyQt6 import QtCore
from PyQt6 import QtGui


class HexTable(QtCore.QAbstractTableModel):
    def __init__(self, parent=None, stream: io.IOBase=None):
        super().__init__(parent)
        self._stream = stream
        self.column = 4
        self.itembyte = 4

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        row = index.row()
        col = index.column()
        if role in {QtCore.Qt.ItemDataRole.DisplayRole}:
            offset = (row * self.column + col) * self.itembyte
            length = self.itembyte
            self._stream.seek(offset)
            value = self._stream.read(length)
            return "0x" + value.hex().zfill(self.itembyte * 2)
        elif role == QtCore.Qt.ItemDataRole.FontRole:
            return QtGui.QFont("Consolas")

    def rowCount(self, _=None):
        self._stream.seek(0, os.SEEK_END)
        return math.ceil(self._stream.tell() / self._bytesPerRow)

    def columnCount(self, _=None):
        return self.column

    # extra methods
    @property
    def _bytesPerRow(self):
        return self.column * self.itembyte
