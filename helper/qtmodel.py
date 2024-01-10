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


def bytes_to_ascii(data: bytes):
    string = [chr(x) if 32 <= x <= 126 else "." for x in data]
    return "".join(string)


def is_cstring(data: bytes):
    return all(32 <= x <= 126 or x == 0 for x in data)


class HexTable(QtCore.QAbstractTableModel):
    show_preview = True

    def __init__(self, parent=None, stream: io.IOBase=None):
        super().__init__(parent)
        self._stream = stream
        self.column = 4
        self.itembyte = 4
        self.viewOffset = 0

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        row = index.row()
        col = index.column()
        if role in {QtCore.Qt.ItemDataRole.DisplayRole}:
            if col < self.column:
                offset = (row * self.column + col) * self.itembyte
                length = self.itembyte
                self._stream.seek(offset + self.viewOffset)
                value = self._stream.read(length)
                return f"0x%0{self.itembyte * 2}x" % int.from_bytes(value, "little")
            else:
                # ascii preview column
                offset = row * self._bytesPerRow
                length = self._bytesPerRow
                self._stream.seek(offset + self.viewOffset)
                value = self._stream.read(length)
                return bytes_to_ascii(value)
        elif role == QtCore.Qt.ItemDataRole.FontRole:
            return QtGui.QFont("Consolas")

    def rowCount(self, _=None):
        self._stream.seek(0, os.SEEK_END)
        return math.ceil((self._stream.tell() - self.viewOffset) / self._bytesPerRow)

    def columnCount(self, _=None):
        return self.column + self.show_preview

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int) -> Any:
        if orientation == QtCore.Qt.Orientation.Horizontal:
            match role:
                case QtCore.Qt.ItemDataRole.DisplayRole:
                    if section < self.column:
                        return hex(section * self.column + self.viewOffset % self._bytesPerRow)
                    else:
                        return "Preview"
                case QtCore.Qt.ItemDataRole.FontRole:
                    return QtGui.QFont("Consolas")
        elif orientation == QtCore.Qt.Orientation.Vertical:
            match role:
                case QtCore.Qt.ItemDataRole.DisplayRole:
                    return hex(section * self._bytesPerRow + self.viewOffset)
                case QtCore.Qt.ItemDataRole.FontRole:
                    return QtGui.QFont("Consolas")

    # extra methods
    @property
    def _bytesPerRow(self):
        return self.column * self.itembyte

    def shiftOffset(self, offset: int):
        self.layoutAboutToBeChanged.emit()

        self.viewOffset = offset

        tl = self.index(0, 0)
        br = self.index(self.rowCount(), self.columnCount())
        self.dataChanged.emit(tl, br)
        self.layoutChanged.emit()


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
    addr = 0
    hex_mode = True

    def child(self, row, parent):
        item = self.itemFromIndex(parent)
        if item is None:
            return None
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
            "address": self._data_addr,
            "addr": self._data_addr,
            "default": self._data_default,
        }
        func = data_funcs.get(tag, data_funcs["default"])
        if func:
            item = self.itemFromIndex(index)
            return func(tag, item, role)

    def _data_default(self, tag, item, role) -> Any:
        match role:
            case QtCore.Qt.ItemDataRole.DisplayRole:
                val = item.get(tag, "")
                if isinstance(val, int) and self.hex_mode:
                    return hex(val)
                else:
                    return str(val)

    def _data_addr(self, tag, item, role) -> Any:
        match role:
            case QtCore.Qt.ItemDataRole.DisplayRole:
                if self.hex_mode:
                    return hex(item["base"] + self.addr)
                else:
                    return str(item["base"] + self.addr)

    def _data_value(self, tag, item, role) -> Any:
        match role:
            case QtCore.Qt.ItemDataRole.DisplayRole:
                val = self._calc_val(item)
                if val is not None:
                    if self.hex_mode:
                        bitsz = item.get("bitsize", 99999) or item["size"] * 8
                        size = min(item["size"], math.ceil(bitsz / 8))
                        return f"0x%0{size * 2}x" % val
                    else:
                        return str(val)
                elif item["size"] == len(item["fields"]):
                    # try display c-string
                    data = bytes((self._calc_val(x) for x in item["fields"]))
                    if is_cstring(data):
                        end = data.index(0) if 0 in data else len(data)
                        cstr = bytes_to_ascii(data[:end])
                        if len(cstr) <= 64:
                            return repr(cstr)
                else:
                    return ""
            case QtCore.Qt.ItemDataRole.FontRole:
                return QtGui.QFont("Consolas")
            case QtCore.Qt.ItemDataRole.ForegroundRole:
                return QtGui.QColor("blue")

    def _calc_val(self, item: StructRecord) -> Any:
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

    def toggleHexMode(self, hexmode: bool):
        self.hex_mode = hexmode
        tl = self.index(0, 0)
        br = self.index(self.rowCount(), self.columnCount())
        self.dataChanged.emit(tl, br)

    def setAddress(self, addr):
        self.addr = addr
