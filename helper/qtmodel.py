import abc
import io
import math
import os
from dataclasses import dataclass
from dataclasses import field
from functools import lru_cache
from typing import Any
from typing import Generic
from typing import Optional
from typing import Self
from typing import TypeVar

from PyQt6 import QtCore
from PyQt6 import QtGui

from modules.pdbparser.parser import StructRecord


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
            return f"0x%0{self.itembyte * 2}x" % int.from_bytes(value, "little")
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


class AbstractTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, root, headers=None, parent=None):
        super().__init__(parent)
        self.headers = headers or []
        self.rootItem = root
        self.parents = {}

    def child(self, row: int, parent: QtCore.QModelIndex) -> Any:
        ...

    def index(self, row, column, parent=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        child_item = self.child(row, parent)
        if child_item is None:
            return QtCore.QModelIndex()
        # if row >= self.rowCount(parent):
        #     return QtCore.QModelIndex()
        index = self.createIndex(row, column, child_item)
        self.parents[index] = parent
        return index

    def itemFromIndex(self, index) -> Any:
        if not index.isValid():
            return self.rootItem
        return index.internalPointer()

    def columnCount(self, index=None) -> int:
        return len(self.headers)

    def parent(self, index) -> QtCore.QModelIndex:
        return self.parents[index]

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole) -> Any:
        """
        you need to reimplement this method for correct data output
        """
        if not index.isValid():
            return None
        return None

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role) -> Any:
        if orientation is QtCore.Qt.Orientation.Vertical:
            return None

        match role:
            case QtCore.Qt.ItemDataRole.DisplayRole:
                return self.headers[section]

    # You should implant/modify the following method for lazylod model

    def rowCount(self, index=QtCore.QModelIndex()) -> int:
        ...

    def canFetchMore(self, parent: QtCore.QModelIndex) -> bool:
        return False


def iter_children(data: Any):
    """function to iterate data children"""
    if isinstance(data, list):
        iter_func = lambda x: enumerate(x)
    elif isinstance(data, dict):
        iter_func = lambda x: x.items()
    else:
        iter_func = lambda x: []

    for x in iter_func(data):
        yield x


@lru_cache
def bitmask(bitcnt):
    return (1 << bitcnt) - 1


class StructTreeModel(AbstractTreeModel):
    raw = b""
    hex_mode = True

    def child(self, row, parent):
        item = self.itemFromIndex(parent)
        for r, (_, x) in enumerate(iter_children(item["fields"])):
            if row == r:
                return x
        return None

    def rowCount(self, index=QtCore.QModelIndex()) -> int:
        if index.column() > 0:
            return 0
        item = self.itemFromIndex(index)
        return len(item["fields"]) if item["fields"] is not None else 0

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        tag = self.headers[index.column()].lower()
        data_funcs = {
            "value": self._data_value,
            "default": self._data_default,
        }
        func = data_funcs.get(tag, data_funcs["default"])
        if func:
            item = self.itemFromIndex(index)
            return func(tag, item, role)

    def _data_default(self, tag, item, role) -> Any:
        match role:
            case QtCore.Qt.ItemDataRole.DisplayRole:
                return str(item.get(tag, ""))

    def _data_value(self, tag, item, role) -> Any:
        match role:
            case QtCore.Qt.ItemDataRole.DisplayRole:
                val = self._calc_val(item)
                if val is not None:
                    bitsz = item.get("bitsize", 99999) or item["size"] * 8
                    size = min(item["size"], math.ceil(bitsz / 8))
                    return f"0x%0{size * 2}x" % val
                else:
                    return ""
            case QtCore.Qt.ItemDataRole.FontRole:
                return QtGui.QFont("Consolas")
            case QtCore.Qt.ItemDataRole.ForegroundRole:
                return QtGui.QColor("blue")

    def _calc_val(self, item: StructRecord):
        base = item["base"]
        size = item["size"]
        if size > 8:
            return None
        boff = item["bitoff"]
        bsize = item["bitsize"]
        raw_len = len(self.raw)
        if base > raw_len or base + size > raw_len:
            return None
        val = int.from_bytes(self.raw[base: base + size], "little")
        if boff and bsize:
            val = (val >> boff) & bitmask(bsize)
        return val

    def loadRaw(self, raw: bytes):
        self.raw = raw
        tl = self.index(0, 0)
        br = self.index(self.rowCount(), self.columnCount())
        self.dataChanged.emit(tl, br)


