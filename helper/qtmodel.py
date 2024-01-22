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
from typing import Protocol
from typing import Self
from typing import TypeVar

from PyQt6 import QtCore
from PyQt6 import QtGui

from modules.pdbparser.pdbparser.pdb import StructRecord


def bytes_to_ascii(data: bytes):
    string = [chr(x) if 32 <= x <= 126 else "." for x in data]
    return "".join(string)


def is_cstring(data: bytes):
    return all(32 <= x <= 126 or x == 0 for x in data)


class Stream(Protocol):
    def seek(self, offset: int, pos: int=os.SEEK_SET, /) -> int:
        ...

    def read(self, size: int) -> bytes:
        ...

    def tell(self) -> int:
        ...


class HexTable(QtCore.QAbstractTableModel):
    show_preview = True

    def __init__(self, stream: Stream, parent=None):
        super().__init__(parent)
        self._stream = stream
        self.column = 4
        self.itembyte = 4
        self.viewOffset = 0  # offset of current buffer
        self.viewAddress = 0  # request address
        self.viewSize = -1  # request size

        self.invalids = set()

    @property
    def streamSize(self):
        if self.viewSize > 0:
            return self.viewSize
        else:
            self._stream.seek(0, os.SEEK_END)
            return self._stream.tell()

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        row = index.row()
        col = index.column()
        if role in {QtCore.Qt.ItemDataRole.DisplayRole}:
            if row == self.rowCount() - 1:
                # last row
                last_col = math.ceil(self.streamSize / self.itembyte) % self.column
            else:
                last_col = -1
            if col < self.column:
                if last_col > 0 and col > last_col:
                    return ""
                offset = self.viewAddress + self.viewOffset + (row * self.column + col) * self.itembyte
                length = self.itembyte
                self._stream.seek(offset)
                try:
                    value = self._stream.read(length)
                    return f"0x%0{self.itembyte * 2}x" % int.from_bytes(value, "little")
                except:
                    self.invalids.add(offset)
                    return ""
            else:
                # ascii preview column
                offset = self.viewAddress + self.viewOffset + row * self._bytesPerRow
                length = self._bytesPerRow if last_col <= 0 else last_col * self.itembyte
                self._stream.seek(offset)
                try:
                    value = self._stream.read(length)
                    return bytes_to_ascii(value)
                except:
                    return ""
        elif role == QtCore.Qt.ItemDataRole.FontRole:
            return QtGui.QFont("Consolas")
        elif role == QtCore.Qt.ItemDataRole.BackgroundRole:
            if not (self.flags(index) & QtCore.Qt.ItemFlag.ItemIsEnabled):
                return QtGui.QColor("#f0d6d5")

    def rowCount(self, _=None):
        return math.ceil((self.streamSize - self.viewOffset) / self._bytesPerRow)

    def columnCount(self, index):
        return self.column + self.show_preview

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int) -> Any:
        if orientation == QtCore.Qt.Orientation.Horizontal:
            match role:
                case QtCore.Qt.ItemDataRole.DisplayRole:
                    if section < self.column:
                        return hex(section * self.itembyte + self.viewOffset % self._bytesPerRow)
                    else:
                        return "Preview"
                case QtCore.Qt.ItemDataRole.FontRole:
                    return QtGui.QFont("Consolas")
        elif orientation == QtCore.Qt.Orientation.Vertical:
            match role:
                case QtCore.Qt.ItemDataRole.DisplayRole:
                    return hex(section * self._bytesPerRow + self.viewOffset + self.viewAddress)
                case QtCore.Qt.ItemDataRole.FontRole:
                    return QtGui.QFont("Consolas")

    def flags(self, index):
        flags = super().flags(index)

        row = index.row()
        col = index.column()
        if col < self.column:
            offset = self.viewAddress + self.viewOffset + (row * self.column + col) * self.itembyte
            if offset in self.invalids:
                flags &= ~QtCore.Qt.ItemFlag.ItemIsEnabled
        else:
            # ascii preview column
            offset = self.viewAddress + self.viewOffset + row * self._bytesPerRow
            length = self._bytesPerRow
            if any(
                x in self.invalids
                for x in range(offset, offset + length, self.itembyte)
            ):
                flags &= ~QtCore.Qt.ItemFlag.ItemIsEnabled

        return flags

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
    headers = []

    def __init__(self, root, parent=None):
        super().__init__(parent)
        self._rootItem = root
        self._parents = {}

    def child(self, row: int, parent: QtCore.QModelIndex) -> Any:
        ...

    def index(self, row, column, parent=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        # if not parent.isValid():
        #     return QtCore.QModelIndex()
        child_item = self.child(row, parent)
        # if row >= self.rowCount(parent):
        #     return QtCore.QModelIndex()
        index = self.createIndex(row, column, child_item)
        self._parents[index] = parent
        return index

    def itemFromIndex(self, index) -> Any:
        if not index.isValid():
            return self._rootItem
        return index.internalPointer()

    def columnCount(self, index=None) -> int:
        return len(self.headers)

    def parent(self, index) -> QtCore.QModelIndex:
        return self._parents[index]

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

    def refresh(self):
        tl = self.index(0, 0)
        br = self.index(self.rowCount(), self.columnCount())
        self.dataChanged.emit(tl, br)

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
    pointerDereferenced = QtCore.pyqtSignal(QtCore.QModelIndex, int)

    fileio = io.BytesIO()
    hex_mode = True
    headers = [
        "Levelname",
        "Value",
        "Type",
        "Size",
        "Count",
        "Address",
    ]

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
        if self.canFetchMore(index):
            return 1
        return len(item["fields"]) if item["fields"] is not None else 0

    def flags(self, index: QtCore.QModelIndex):
        flags = super().flags(index)

        tag = self.headers[index.column()].lower()
        item = self.itemFromIndex(index)
        if tag == "value":
            flags |= QtCore.Qt.ItemFlag.ItemIsEditable
        elif tag == "count":
            if item["is_pointer"]:
                flags |= QtCore.Qt.ItemFlag.ItemIsEditable
        elif tag == "type":
            if item[tag].lower().endswith("pvoid"):
                flags |= QtCore.Qt.ItemFlag.ItemIsEditable
        return flags

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        tag = self.headers[index.column()].lower()
        item = self.itemFromIndex(index)
        match role:
            case QtCore.Qt.ItemDataRole.DisplayRole:
                match tag:
                    case "value":
                        val = self._calc_val(item)
                        if val is not None:
                            if self.hex_mode:
                                bitsz = item.get("bitsize", 99999) or item["size"] * 8
                                size = min(item["size"], math.ceil(bitsz / 8))
                                return f"0x%0{size * 2}x" % val
                            else:
                                return str(val)
                        elif item["fields"] and item["size"] == len(item["fields"]):
                            # try display c-string
                            values = [self._calc_val(x) for x in item["fields"]]
                            if all(x is not None for x in values):
                                data = bytes(values)
                                if is_cstring(data):
                                    end = data.index(0) if 0 in data else len(data)
                                    cstr = bytes_to_ascii(data[:end])
                                    if len(cstr) <= 64:
                                        return repr(cstr)
                        else:
                            return ""
                    case "count":
                        if isinstance(item["fields"], list):
                            return str(len(item["fields"]))
                        if item["is_pointer"]:
                            return 1
                    case _:
                        val = item.get(tag, "")
                        if isinstance(val, int) and self.hex_mode:
                            return hex(val)
                        else:
                            return str(val)
            case QtCore.Qt.ItemDataRole.FontRole:
                if tag in {"value", "count"}:
                    return QtGui.QFont("Consolas")
            case QtCore.Qt.ItemDataRole.ForegroundRole:
                if tag == "value":
                    old_val = item["value"]
                    new_val = self._calc_val(item)
                    if old_val != new_val:
                        item["value"] = new_val
                        return QtGui.QColor("red")
                if self.flags(index) & QtCore.Qt.ItemFlag.ItemIsEditable:
                    return QtGui.QColor("blue")

    def setData(self, index: QtCore.QModelIndex, value: Any, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> bool:
        ...

    def _calc_val(self, item: StructRecord) -> Any:
        base = item["address"]
        size = item["size"]
        if size > 8:
            return None
        boff = item["bitoff"]
        bsize = item["bitsize"]
        self.fileio.seek(base)
        val = int.from_bytes(self.fileio.read(size), "little")
        if boff and bsize:
            val = (val >> boff) & bitmask(bsize)
        return val

    def insertRows(self, row: int, count: int, parent: QtCore.QModelIndex):
        item = self.itemFromIndex(parent)

        self.beginInsertRows(parent, row, row + count)
        if "fields" not in item or item["fields"] is None:
            item["fields"] = []
        for _ in range(count):
            item["fields"].insert(row, {})
        self.endInsertRows()

        return True

    def canFetchMore(self, parent: QtCore.QModelIndex) -> bool:
        item = self.itemFromIndex(parent)
        return (
            item.get("is_pointer", False)
            and (item["fields"] is None or item["fields"] == "")
        )

    def fetchMore(self, parent: QtCore.QModelIndex) -> None:
        self.insertRow(0, parent)
        index = self.index(0, 0, parent)
        item = self.itemFromIndex(index)
        item.update(self.itemFromIndex(parent))
        item["levelname"] = "loading..."
        item["is_pointer"] = False
        item["fields"] = None
        self.dataChanged.emit(index, index)
        self.pointerDereferenced.emit(parent, self._calc_val(item))

    def appendItem(self, record: dict, parent=QtCore.QModelIndex()):
        last_row = self.rowCount()
        self.insertRow(last_row, parent)
        item = self.itemFromIndex(self.index(last_row, 0, parent))
        item.update(record)

    def setItem(self, record: dict, index=QtCore.QModelIndex()):
        item = self.itemFromIndex(index)
        rc = len(item["fields"]) if item["fields"] is not None else 0
        new_count = len(record["fields"]) if record["fields"] else 0
        if new_count < rc:
            return
        self.insertRows(rc, new_count - rc, index)
        item.update(record)
        self.dataChanged.emit(index, index)

    def loadStream(self, fileio: Stream):
        self.fileio = fileio
        self.refresh()

    def toggleHexMode(self, hexmode: bool):
        self.hex_mode = hexmode
        self.refresh()
