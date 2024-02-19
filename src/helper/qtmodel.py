import io
import math
import os
from collections import defaultdict
from contextlib import suppress
from functools import lru_cache
from pathlib import Path
from typing import Any
from typing import Protocol
from typing import Sequence
from typing import Union

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6 import QtWidgets


def bytes_to_ascii(data: bytes):
    string = [chr(x) if 32 <= x <= 126 else "." for x in data]
    return "".join(string)


def is_cstring(data: bytes):
    if 0 in data:
        data = data[: data.index(0)]
    return all(32 <= x <= 126 for x in data)


class Stream(Protocol):
    def seek(self, offset: int, pos: int=os.SEEK_SET, /) -> int:
        ...

    def read(self, size: int) -> bytes:
        ...

    def write(self, buf: bytes, /) -> int:
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

    def rowCount(self, _=QtCore.QModelIndex()):
        return math.ceil((self.streamSize - self.viewOffset) / self._bytesPerRow)

    def columnCount(self, index=QtCore.QModelIndex()):
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
        if fn := getattr(self, "post_init", None):
            fn()

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

    def refresh(self, index=QtCore.QModelIndex()):
        tl = self.index(0, 0, index)
        br = self.index(self.rowCount(index) - 1, 0, index)
        while not self.canFetchMore(br) and (r := self.rowCount(br)):
            br = self.index(r - 1, 0, br)
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


def _calc_val(fileio: Stream, item: dict) -> Any:
    if not item.get("_refresh_requested", False) and item.get("value", None):
        # return cached value unless _refresh_requested set to True
        return item["value"]

    base = item["address"]
    size = item["size"]
    if size > 8:
        return None
    boff = item["bitoff"]
    bsize = item["bitsize"]

    fileio.seek(base)
    try:
        val = int.from_bytes(fileio.read(size), "little", signed=item.get("has_sign", False))
        item["_is_invalid"] = False
    except:
        item["_is_invalid"] = True
        return 0
    if boff is not None and bsize is not None:
        val = (val >> boff) & bitmask(bsize)

    old_value = item.get("value", None)
    item["_changed_since_prev"] = old_value is not None and old_value != val
    item["_refresh_requested"] = False
    item["value"] = val

    return val


class StructTreeModel(AbstractTreeModel):
    pointerDereferenced = QtCore.pyqtSignal(QtCore.QModelIndex, object, int)
    pvoidStructChanged = QtCore.pyqtSignal(QtCore.QModelIndex, object, int, str)

    headers = [
        "Levelname",
        "Value",
        "Type",
        "Size",
        "Count",
        "Address",
    ]

    def post_init(self):
        self.fileio = io.BytesIO()
        self.hex_mode = True
        self.allow_dereferece_pointer = False
        self._value_version = 0

    def child(self, row, parent):
        item = self.itemFromIndex(parent)
        for r, (_, x) in enumerate(iter_children(item.get("fields", None))):
            if row == r:
                return x
        return None

    def rowCount(self, index=QtCore.QModelIndex()) -> int:
        if index.column() > 0:
            return 0
        item = self.itemFromIndex(index)
        if self.canFetchMore(index):
            return 1

        if isinstance(item["fields"], list):
            # TreeView calls `rowCount` before `index`
            # so just make a psuedo internal layer here
            child_cnt = len(item["fields"])
            if child_cnt > 100:
                item["_count"] = child_cnt
                childs = item["fields"]
                item["fields"] = []
                for off in range(0, child_cnt, 100):
                    fake_layer = childs[0].copy()
                    fake_layer["expr"] = ""
                    cnt = min(child_cnt, off + 99) - off + 1
                    fake_layer["levelname"] = "[%d:%d]" % (off, min(child_cnt - 1, off + 99))
                    fake_layer["size"] = cnt * fake_layer["size"]
                    fake_layer["fields"] = childs[off: off + 100]
                    item["fields"].append(fake_layer)

        return len(item["fields"]) if item["fields"] is not None else 0

    def flags(self, index: QtCore.QModelIndex):
        flags = super().flags(index)

        tag = self.headers[index.column()].lower()
        item = self.itemFromIndex(index)

        if tag == "value":
            flags |= QtCore.Qt.ItemFlag.ItemIsEditable
        elif tag == "count":
            p_item = self.itemFromIndex(self.parent(index))
            if item["is_pointer"] and self.allow_dereferece_pointer:
                if not isinstance(p_item.get("fields", None), list):
                    # not in array
                    if not item["type"].lower().endswith("pvoid"):
                        # only allow non-pvoid pointer be editable
                        flags |= QtCore.Qt.ItemFlag.ItemIsEditable
        elif tag == "type" and self.allow_dereferece_pointer:
            if item[tag].lower().endswith("pvoid") or item.get("_is_pvoid", False):
                flags |= QtCore.Qt.ItemFlag.ItemIsEditable

        if flags & QtCore.Qt.ItemFlag.ItemIsEditable:
            if item.get("_is_invalid", False):
                flags &= ~QtCore.Qt.ItemFlag.ItemIsEnabled

        return flags

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        tag = self.headers[index.column()].lower()
        item = self.itemFromIndex(index)
        match role:
            case QtCore.Qt.ItemDataRole.DisplayRole | QtCore.Qt.ItemDataRole.EditRole:
                match tag:
                    case "value":
                        if item["fields"] and item["size"] == len(item["fields"]):
                            # try display c-string
                            values = [_calc_val(self.fileio, x) for x in item["fields"]]
                            if all(x is not None for x in values):
                                data = bytes(values)
                                if is_cstring(data):
                                    end = data.index(0) if 0 in data else len(data)
                                    cstr = bytes_to_ascii(data[:end])
                                    if len(cstr) <= 64:
                                        return repr(cstr)
                        val = _calc_val(self.fileio, item)
                        if val is not None:
                            if self.hex_mode:
                                bitsz = item.get("bitsize", None) or item["size"] * 8
                                size = min(item["size"], math.ceil(bitsz / 8))
                                return f"{{:#0{size * 2 + 2}x}}".format(val)
                            else:
                                return str(val)
                        else:
                            return ""
                    case "count":
                        if isinstance(item["fields"], list):
                            return item.get("_count", len(item["fields"]))
                        if item["is_pointer"] and self.allow_dereferece_pointer:
                            return item.get("_count", 1)
                    case _:
                        val = item.get(tag, "")
                        if isinstance(val, int) and self.hex_mode:
                            return hex(val)
                        else:
                            return str(val)
            case QtCore.Qt.ItemDataRole.ToolTipRole:
                return item.get("expr", None)
            case QtCore.Qt.ItemDataRole.FontRole:
                if tag in {"value", "count", "address"}:
                    return QtGui.QFont("Consolas")
            case QtCore.Qt.ItemDataRole.ForegroundRole:
                # QTreeView request order:
                #   - ForegroundRole
                #   - DisplayRole, if we _calc_val here, ForegroundRole will be updated in the next cycle
                #   - BackgroundRole
                _calc_val(self.fileio, item)  # update value in advanced to render correct color
                if not (self.flags(index) & QtCore.Qt.ItemFlag.ItemIsEnabled):
                    return
                if tag == "value":
                    if item.get("_changed_since_prev", False):
                        return QtGui.QColor("red")
                if self.flags(index) & QtCore.Qt.ItemFlag.ItemIsEditable:
                    return QtGui.QColor("blue")
            case QtCore.Qt.ItemDataRole.BackgroundRole:
                if not (self.flags(index) & QtCore.Qt.ItemFlag.ItemIsEnabled):
                    return QtGui.QColor("#f0d6d5")
            case QtCore.Qt.ItemDataRole.DecorationRole:
                if index.column() == 0:
                    return QtGui.QIcon(":icon/images/vswin2019/Field_left_16x.svg")

    def setData(self, index: QtCore.QModelIndex, value: Any, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> bool:
        tag = self.headers[index.column()].lower()
        item = self.itemFromIndex(index)
        if tag == "value":
            try:
                val = eval(value)
            except:
                return False
            base = item["address"]
            size = item["size"]
            boff = item["bitoff"]
            bsize = item["bitsize"]

            self.fileio.seek(base)
            old_val = self.fileio.read(size)
            if boff and bsize:
                val = (val & bitmask(bsize))
                new_val = old_val & ~(bitmask(bsize) << boff)
                new_val |= val << boff
            else:
                new_val = val
            if new_val == old_val:
                return False

            if not item.get("has_sign", False) and val < 0:
                # cannot set a negative value to an unsigned type int
                return False

            item["value"] = val
            self.fileio.write(new_val.to_bytes(size, "little", signed=item.get("has_sign", False)))
            return True
        elif tag == "type":
            old_value = item.get(tag, "")
            if value == old_value:
                return False
            item["_is_pvoid"] = True
            item[tag] = value
            count = item.get("_count", 1)
            self.pvoidStructChanged.emit(index, _calc_val(self.fileio, item), count, value)
            return True
        elif tag == "count":
            old_value = item.get("_count", 1)
            if value == old_value or value <= 0:
                return False
            item["_count"] = value
            self.pointerDereferenced.emit(index, _calc_val(self.fileio, item), value)
            return True
        return False

    def insertRows(self, row: int, count: int, parent: QtCore.QModelIndex):
        item = self.itemFromIndex(parent)

        self.beginInsertRows(parent, row, row + count - 1)
        if "fields" not in item or item["fields"] is None:
            item["fields"] = []
        for _ in range(count):
            item["fields"].insert(row, {})
        self.endInsertRows()

        return True

    def removeRows(self, row: int, count: int, parent=QtCore.QModelIndex()) -> bool:
        item = self.itemFromIndex(parent)

        if "fields" not in item or item["fields"] is None:
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        if row == 0 and count == self.rowCount(parent):
            item["fields"] = None
        else:
            if isinstance(item["fields"], dict):
                keys = [x[0] for x in iter_children(item["fields"])]
                remove_keys = keys[row: row + count]
                for k in reversed(remove_keys):
                    del item["fields"][k]
            elif isinstance(item["fields"], list):
                item["fields"] = item["fields"][:row] + item["fields"][row+count:]
        self.endRemoveRows()

        return True

    def canFetchMore(self, parent: QtCore.QModelIndex) -> bool:
        if not self.allow_dereferece_pointer:
            return False
        item = self.itemFromIndex(parent)
        return (
            not item["type"].lower().endswith("pvoid")
            and item.get("is_pointer", False)
            and (item["fields"] is None or item["fields"] == "")
        )

    def fetchMore(self, parent: QtCore.QModelIndex) -> None:
        self.insertRow(0, parent)
        index = self.index(0, 0, parent)
        item = self.itemFromIndex(index)
        item.update(self.itemFromIndex(parent))
        item["levelname"] = "loading..."
        # item["is_pointer"] = False
        item["fields"] = None
        self.dataChanged.emit(index, index)
        self.pointerDereferenced.emit(parent, _calc_val(self.fileio, item), item.get("_count", 1))

    def appendItem(self, record: dict, parent=QtCore.QModelIndex()):
        last_row = self.rowCount()
        self.insertRow(last_row, parent)
        item = self.itemFromIndex(self.index(last_row, 0, parent))
        item.update(record)

    def setItem(self, record: dict, index=QtCore.QModelIndex()):
        item = self.itemFromIndex(index)
        new_count = len(record["fields"]) if record["fields"] else 0
        if row_count := self.rowCount(index):
            self.removeRows(0, row_count - 1, index)
        if new_count:
            self.layoutAboutToBeChanged.emit()
            self.beginInsertRows(index, 0, new_count - 1)
            item.update(record)
            self.endInsertRows()
            self.layoutChanged.emit()

    def refreshIndex(self, index=QtCore.QModelIndex()):
        item = self.itemFromIndex(index)

        def _clear_value(r: dict):
            r["_refresh_requested"] = True
            for _, c in iter_children(r["fields"]):
                _clear_value(c)

        _clear_value(item)
        self.refresh(index)

    def loadStream(self, fileio: Stream):
        self.fileio = fileio
        self.refresh()

    def toggleHexMode(self, hexmode: bool):
        self.hex_mode = hexmode
        self.refresh()


class BorderItemDelegate(QtWidgets.QStyledItemDelegate):
    color = QtGui.QColor("#d8d8d8")

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        line = QtCore.QLine(option.rect.topRight(), option.rect.bottomRight())

        painter.save()
        painter.setPen(self.color)
        painter.drawLine(line)
        painter.restore()


class StructTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data: list, parent=None):
        super().__init__(parent)
        self.fileio = io.BytesIO()
        self.hex_mode = True
        self.char_mode = False
        self._data = data
        if isinstance(data, list) and data != []:
            self.titles = [x["expr"].replace(".", "\n.").lstrip() for x in data[0]]
        else:
            self.titles = []

    def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if role == QtCore.Qt.ItemDataRole.DisplayRole: # only change what DisplayRole returns
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return self.titles[section]
            elif orientation == QtCore.Qt.Orientation.Vertical:
                return str(section + 1)
        return super().headerData(section, orientation, role) # must have this line

    def data(self, index: QtCore.QModelIndex, role=QtCore.Qt.ItemDataRole.DisplayRole):
        row = index.row()
        col = index.column()
        item = self._data[row][col]
        if role in {QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.EditRole}:
            val = _calc_val(self.fileio, item)
            if val is not None:
                if self.char_mode:
                    raw = val.to_bytes(item["size"], "little")
                    return str(raw)
                elif self.hex_mode:
                    bitsz = item.get("bitsize", None) or item["size"] * 8
                    size = min(item["size"], math.ceil(bitsz / 8))
                    return f"{{:#0{size * 2 + 2}x}}".format(val)
                else:
                    return str(val)
            else:
                return ""
        elif role == QtCore.Qt.ItemDataRole.FontRole:
            return QtGui.QFont("Consolas")
        elif role == QtCore.Qt.ItemDataRole.ForegroundRole:
            # QTableView request order:
            #   - ForegroundRole
            #   - DisplayRole, if we _calc_val here, ForegroundRole will be updated in the next cycle
            #   - BackgroundRole
            _calc_val(self.fileio, item)  # update value in advanced to render correct color
            if not (self.flags(index) & QtCore.Qt.ItemFlag.ItemIsEnabled):
                return
            if item.get("_changed_since_prev", False):
                return QtGui.QColor("red")
            # if self.flags(index) & QtCore.Qt.ItemFlag.ItemIsEditable:
            #     return QtGui.QColor("blue")

    def flags(self, index: QtCore.QModelIndex):
        flags = super().flags(index)
        flags |= QtCore.Qt.ItemFlag.ItemIsEditable
        return flags

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._data[0]) if self.rowCount() else 0

    def refresh(self):
        tl = self.index(0, 0)
        br = self.index(self.rowCount() - 1, self.columnCount() - 1)
        self.dataChanged.emit(tl, br)

    def loadStream(self, fileio: Stream):
        self.fileio = fileio
        self.refresh()

    def toggleHexMode(self, hexmode: bool):
        self.hex_mode = hexmode
        self.refresh()

    def toggleCharMode(self, charmode: bool):
        self.char_mode = charmode
        self.refresh()


def get_icon(filename):
    fileInfo = QtCore.QFileInfo(filename)
    iconProvider = QtWidgets.QFileIconProvider()
    return iconProvider.icon(fileInfo)


class FileExplorerModel(AbstractTreeModel):

    headers = ["File"]

    def post_init(self):
        self.requestPaths = set()
        self.pathIndexes = {}
        self.folders = defaultdict(list)

    def index(self, row, column, parent=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        ind = super().index(row, column, parent)
        item = self.itemFromIndex(ind)
        self.pathIndexes[item] = ind
        return ind

    def child(self, row: int, parent: QtCore.QModelIndex) -> Any:
        item = self.itemFromIndex(parent)
        items = self.folders.get(item, [])
        return items[row]

    def rowCount(self, index=QtCore.QModelIndex()) -> int:
        item = self.itemFromIndex(index)
        items = self.folders.get(item, [])
        return len(items)

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole) -> Any:
        item = self.itemFromIndex(index)
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            folder_index = self.parent(index)
            folder = self.itemFromIndex(folder_index)
            try:
                return str(item.relative_to(folder))
            except:
                return str(item)
        elif role == QtCore.Qt.ItemDataRole.ToolTipRole:
            return str(item)
        elif role == QtCore.Qt.ItemDataRole.DecorationRole:
            if item.suffix == ".pdbin":
                return QtGui.QIcon(":icon/images/vswin2019/Database_16x.svg")
            else:
                return get_icon(str(item))

    def insertRows(self, row: int, count: int, parent: QtCore.QModelIndex):
        item = self.itemFromIndex(parent)

        folder = self.folders.get(item, None)
        if folder is None:
            return False

        self.beginInsertRows(parent, row, row + count - 1)
        for _ in range(count):
            folder.insert(row, {})
        self.endInsertRows()

        return True

    def _insert_folder(self, folder: Path):
        with suppress(KeyError):
            return self.pathIndexes[folder]

        root = self.itemFromIndex(QtCore.QModelIndex())
        most_common_path = Path(".")
        for f in self.folders.keys():
            if f == root:
                continue
            comm_path = os.path.commonpath((f, folder))
            if comm_path > str(most_common_path):
                most_common_path = Path(comm_path)

        # insert new common folder node
        self.layoutAboutToBeChanged.emit()
        try:
            parent = self.pathIndexes[most_common_path]
            closest_folder = most_common_path
        except:
            parent = QtCore.QModelIndex()
            for f in most_common_path.parents:
                with suppress(KeyError):
                    parent = self.pathIndexes[f]
                    break
            closest_folder = self.itemFromIndex(parent)
            r = self.rowCount(parent)
            for child in self.folders[closest_folder]:
                self.folders[folder].append(child)
            self.folders[closest_folder] = []

        r = self.rowCount(parent)
        self.folders[closest_folder].append(folder)
        parent = self.index(r, 0, parent)
        self.layoutChanged.emit()

        return parent

    def _insert_file(self, file: Path):
        if file in self.requestPaths:
            return self.pathIndexes[file]
        self.requestPaths.add(file)
        parent = self._insert_folder(file.parent)
        folder = self.itemFromIndex(parent)

        r = self.rowCount(parent)
        self.beginInsertRows(parent, r, r)
        self.folders[folder].append(file)
        self.endInsertRows()

        return self.index(r, 0, parent)

    def addFiles(self, files: Sequence[Union[str, Path]]) -> list[QtCore.QModelIndex]:
        indexes = []
        for f in files:
            index = self._insert_file(Path(f).resolve())
            indexes.append(index)

        return indexes
