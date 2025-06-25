import logging
import os
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from typing import Self
from typing import TypedDict

from construct import Struct
from PyQt6 import QtWidgets

from ctrl.qtapp import HistoryMenu
from ctrl.qtapp import MenuAction
from ctrl.qtapp import Plugin
from ctrl.WidgetPicklePdb import PicklePdb
from helper import qtmodel
from modules.expr_parser import InvalidExpression
from modules.expr_parser import query_struct_from_expr
from modules.pdbparser.pdbparser import pdb
from modules.pdbparser.pdbparser import picklepdb
from modules.utils.myfunc import BITMASK
from modules.utils.myfunc import escape_filename
from modules.utils.typ import Stream

logger = logging.getLogger(__name__)


class ViewStruct(TypedDict):
    # pdb.StructRecord
    levelname: str
    value: int | None
    type: str
    address: int
    size: int
    bitoff: int | None
    bitsize: int | None
    fields: list[Self] | dict[str, Self] | None
    is_pointer: bool
    is_funcptr: str
    has_sign: bool
    lf: Struct | None

    expr: str


def _read_value(item: ViewStruct, stream: Stream | None) -> int:
    if stream is None:
        return -1
    if item["value"] is not None:
        # for literal number, value will be the number
        return item["value"]
    base = item["address"]
    size = item["size"]
    boff = item["bitoff"]
    bsize = item["bitsize"]

    stream.seek(base)
    val = int.from_bytes(stream.read(size), "little")
    if boff is not None and bsize is not None:
        val = (val >> boff) & BITMASK(bsize)
    return val


@dataclass
class CStruct:
    _record: ViewStruct
    _stream: qtmodel.Stream | None

    def __getattr__(self, field: str):
        if not isinstance(self._record["fields"], dict):
            raise InvalidExpression("Member not found: %r" % field)
        return CStruct(self._record["fields"][field], self._stream)

    def __getitem__(self, index: int):
        if not isinstance(self._record["fields"], list):
            raise InvalidExpression("Index not found: %r" % index)
        return CStruct(self._record["fields"][index], self._stream)

    def __iter__(self):
        if isinstance(self._record["fields"], list):
            for key, item in enumerate(self._record["fields"].__iter__()):
                yield key, CStruct(item, self._stream)
        if isinstance(self._record["fields"], dict):
            for key, item in self._record["fields"].items():
                yield key, CStruct(item, self._stream)
    
    def __str__(self):
        if self._record["levelname"]:
            return self._record["levelname"]
        else:
            return repr(self)

    def __repr__(self):
        fields = self._record["fields"]
        if isinstance(fields, list):
            flen = len(fields)
            display_fields = ["%d=..." % i for i in range(flen)][:10]
            fields_txt = ", ".join(display_fields)
            if len(display_fields) != flen:
                fields_txt += ", ..., %d=..." % flen
            fields_txt = "[%s]" % fields_txt
        elif isinstance(fields, dict):
            fields_txt = ", ".join(["%s=..." % k for k in fields])
            fields_txt = "{%s}" % fields_txt
        else:
            fields_txt = "()"
        return "{}{}".format(
            self._record["type"],
            fields_txt,
        )

    def __int__(self) -> int:
        if self._stream is None:
            return -1
        return _read_value(self._record, self._stream)

    @property
    def is_plist(self):
        typ = self._record["type"]
        return typ.lower() == 'plist_struct'
 
    def iter_plist_nodes(self):
        if not self.is_plist:
            raise TypeError("only applicable for PLIST_STRUCT, current type is %r" % self._field["type"])
        if self._stream is None:
            raise ValueError("Need _stream for this operation.")
        head = self.head.next
        size = int(self.size)
        nodes = []
        for i in range(size):
            if i > 0 and hex(int(head)) == int(self.head.next):
                raise ValueError("shall has %d elements in list: %s, got length = %d!" % (size, repr(nodes), len(nodes)))
            nodes.append(hex(int(head)))
            yield head
            # deref head->next manually here
            self._stream.seek(int(head))
            new_node = self._stream.read(self.head._record["size"])
            head = CStruct(head._record.copy(), self._stream)
            head._record["value"] = int.from_bytes(new_node[:head._record["size"]], "little")

    def iter_items(self, _record=None):
        """generator of recursive (expr: str, record: ViewStruct) pairs"""
        record = self._record if _record is None else _record
        fields = record["fields"]
        if fields is None:
            yield record["expr"], _read_value(record, self._stream)
        elif len(fields) == 0:
            yield record["expr"], _read_value(record, self._stream)
        elif isinstance(fields, list):
            for x in fields:
                yield from self.iter_items(x)
        elif isinstance(fields, dict):
            for x in fields.values():
                yield from self.iter_items(x)

    def get_size(self) -> int:
        return self._record["size"]

    def get_type(self) -> str:
        return self._record["type"]

    def get_addr(self) -> int:
        return self._record["address"]

    def get_short_name(self) -> str:
        return self._record["expr"]

    def dump(self, filename, show_type=False, progress_bar=False):
        """
        dump all struct fields to `filename`,
        @param `show_type`, set to `True` may slow down process
        @param `progress_bar`, set to `True` to display dots as progress bar
        """
        filename = escape_filename(filename)
        with open(filename, "w") as fs:
            for expr, val in self.iter_items():
                # print("expr={}, val={}".format(expr, val))
                expr_type = " (" + self._record["type"] + ")" if show_type else ""
                if self._record["is_funcptr"]:
                    fs.write("{:90} = {}\n".format(expr + expr_type, self._record["levelname"]))
                else:
                    fs.write("{:90} = {}\n".format(expr + expr_type, hex(val)))


def _shift_addr(s: pdb.StructRecord, shift: int=0):
    s["address"] = s["address"] + shift
    if isinstance(s["fields"], dict):
        for c in s["fields"].values():
            _shift_addr(c, shift)
    elif isinstance(s["fields"], list):
        for c in s["fields"]:
            _shift_addr(c, shift)


def _add_expr(s: pdb.StructRecord, expr: str):
    if expr.endswith("->") or expr.endswith("."):
        notation = ""
    else:
        notation = "->" if s.get("is_pointer", False) else "."
    s["expr"] = expr.rstrip(notation)
    if isinstance(s["fields"], dict):
        for c in s["fields"].values():
            _add_expr(c, expr + notation + c["levelname"])
    elif isinstance(s["fields"], list):
        for c in s["fields"]:
            _add_expr(c, expr + c["levelname"])


def _flatten_dict(s: pdb.StructRecord, out: list):
    childs = s.get("fields", None)
    s["fields"] = None
    if isinstance(childs, dict):
        for c in childs.values():
            _flatten_dict(c, out)
    elif isinstance(childs, list):
        for c in childs:
            _flatten_dict(c, out)
    else:
        out.append(s)


def _remove_extra_paren(expr: str) -> str:
    expr = expr.strip()
    while expr.startswith("(") and expr.endswith(")"):
        expr = expr[1: -1].strip()
    return expr


class LoadPdb(Plugin):
    _pdb: pdb.PDB7 = None
    _loading: bool = False

    def registerMenues(self) -> list[MenuAction]:
        return [
            {
                "name": self.tr("PDB"),
                "submenus": [
                    {
                        "name": self.tr("Generate PDB..."),
                        "command": "ShowPicklePdb",
                        "icon": ":icon/images/vswin2019/Database_16x.svg",
                    },
                    {
                        "name": self.tr("Recently PDBs"),
                        "submenus": [],
                    },
                    {"name": "---",},
                    {
                        "name": self.tr("Show PDB status..."),
                        "command": "ShowPdbStatus",
                    },
                ]
            },
        ]

    def registerCommands(self):
        return [
            ("ShowPdbStatus", self.show_status),
            ("ShowPicklePdb", self.show_pickle_pdb),
        ]

    def post_init(self):
        self.widget = None
        self.app.evt.add_hook("ApplicationClosed", self._onClosed)

        self._pdb_fname = ""
        current_pdb = self.app.app_setting.value("LoadPdb/pdbin", "")

        menu = self.app.menu(self.tr("Recently PDBs"))
        _recently_used = self.app.app_setting.value("LoadPdb/recent_used", [])
        _recently_used = [x for x in _recently_used if os.path.exists(x)]
        self._hist_pdbs = HistoryMenu(menu, _recently_used, default=current_pdb)
        self._hist_pdbs.actionTriggered.connect(lambda _f: self.load_pdbin(_f))
        self._hist_pdbs.cleared.connect(lambda: self.app.app_setting.remove("LoadPdb/recent_used"))

        if current_pdb:
            self.load_pdbin(current_pdb)

    def _onClosed(self, evt):
        if self.widget:
            self.widget.close()

    def load_pdbin(self, filename=""):
        if not filename:
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                self.app,
                caption="Open File",
                filter="Any (*.*)"
            )
        if filename:
            logger.debug("loadpdb: %r", filename)

            self._hist_pdbs.add_data(filename)
            self.app.app_setting.setValue("LoadPdb/recent_used", list(self._hist_pdbs.data_list))

            def _cb(_pdb):
                if _pdb is None:
                    self.app.statusBar().showMessage("Pdbin load failed!")
                    return
                self.app.app_setting.setValue("LoadPdb/pdbin", filename)
                self._pdb_fname = filename
                self._pdb = _pdb
                self._loading = False
                self.app.statusBar().showMessage("Pdbin is Loaded.")
                self.app.log("PDB is loaded!")

            def _err(expt, tb):
                self._hist_pdbs.remove_data(filename)
                QtWidgets.QMessageBox.warning(
                    self.app,
                    self.__class__.__name__,
                    str(expt),
                )

            path = Path(filename)
            if path.suffix == ".pdbin":
                self.app.exec_async(
                    picklepdb.load_pdbin,
                    filename,
                    finished_cb=_cb,
                    errored_cb=_err,
                )
            elif path.suffix == ".pdb":
                self.app.exec_async(
                    pdb.parse,
                    filename,
                    finished_cb=_cb,
                    errored_cb=_err,
                )
            self._loading = True
            self.app.statusBar().showMessage("Loading... %r" % filename)

    def is_loading(self):
        return self._loading

    def show_pickle_pdb(self):
        if self.widget is None:
            self.widget = PicklePdb(self.app)
            self.widget.loaded.connect(lambda f: self.load_pdbin(f))
        self.widget.show()
        self.widget.activateWindow()

    def show_status(self):
        if self._pdb_fname:
            QtWidgets.QMessageBox.information(
                self.app,
                "PDB Status",
                "Loaded File: %r" % self._pdb_fname,
            )
        else:
            QtWidgets.QMessageBox.warning(
                self.app,
                "PDB Status",
                "Not loaded",
            )

    def get_global_symbols(self) -> dict[str, int]:
        symbols = {}
        for name in self._pdb.glb_stream.symbols.keys():
            if name.startswith("_") or name.endswith("$"):
                # exclude built-in special symbols
                continue
            try:
                _, off = self._pdb._get_glb(name)
            except IndexError:
                print(name)
            else:
                symbols[name] = off
        return symbols

    def _duplicate_as_array(self, expr: str, s: pdb.StructRecord, count: int) -> ViewStruct:
        if count > 1:
            s["levelname"] = "[0]"
            childs = [s]
            backup = pickle.dumps(s)
            for n in range(1, count):
                copied = pickle.loads(backup)
                copied["levelname"] = "[%d]" % n
                _shift_addr(copied, n * s["size"])
                childs.append(copied)
            s = pdb.new_struct(
                levelname="%s[%d]" % (expr, count),
                type="LF_ARRAY",
                address=s["address"],
                size=count * s["size"],
                fields=childs,
            )
        else:
            s["levelname"] = expr
        _add_expr(s, expr)
        return s

    def parse_expr_to_struct(self, expr: str, addr=0, count=0, data_size=0, add_dummy_root=False) -> pdb.StructRecord:
        if expr == "":
            return pdb.new_struct()

        s = query_struct_from_expr(self._pdb, expr, addr)
        if count == 0:
            count = data_size // s["size"]
        s = self._duplicate_as_array(expr, s, count)

        if add_dummy_root:
            s = pdb.new_struct(
                fields=[s],
            )
        return s

    def _tabulate_a_struct(self, struct: pdb.StructRecord, count: int, total_byte: int) -> list[ViewStruct]:
        if isinstance(struct["fields"], list):
            array = []
            if count == 0:
                count = len(struct["fields"])
            for x in struct["fields"][: count]:
                cut_pos = len(x["levelname"])
                row = []
                _flatten_dict(x, row)
                for c in row:
                    c["expr"] = c["expr"][cut_pos:]
                array.append(row)
        else:
            backup = pickle.dumps(struct)
            if count == 0:
                count = total_byte // struct["size"]
            array = []
            for n in range(max(1, count)):
                copied = pickle.loads(backup)
                copied["levelname"] = "[%d]" % n
                _shift_addr(copied, n * struct["size"])
                _add_expr(copied, "")
                row = []
                _flatten_dict(copied, row)
                array.append(row)
        return array

    def parse_expr_to_table(self, expr: str, addr=0, count=0, data_size=0) -> list[ViewStruct]:
        out_struct = query_struct_from_expr(self._pdb, expr, addr)
        _add_expr(out_struct, "")
        array = self._tabulate_a_struct(out_struct, count, data_size)
        return array

    def query_struct(self, expr: str, virtual_base: int | None=0, io_stream=None) -> ViewStruct:
        if virtual_base is None:
            raise ValueError(self.tr("`virtual_base` is None! Maybe forgot to attach to a live process?"))
        struct = query_struct_from_expr(self._pdb, expr, virtual_base, io_stream)
        struct["levelname"] = expr
        _add_expr(struct, expr)
        return struct

    def deref_struct(self, struct: ViewStruct, io_stream: Stream, count=1, casting=False) -> ViewStruct:
        if count == 0:
            raise ValueError("Deref count at least 1, got: %d" % count)
        _type = _remove_extra_paren(struct["type"])
        addr = struct["value"] or _read_value(struct, io_stream)
        expr = "*((%s)%d)" % (_type, addr)
        out_struct = query_struct_from_expr(self._pdb, expr, io_stream=io_stream)

        _expr = _remove_extra_paren(struct.get("expr", "") or "")
        if casting:
            _expr = "(%s)%s" % (_type, _expr)
        if count == 1:
            if _expr.startswith("("):
                _expr = "(%s)->" % _expr
            else:
                _expr = "%s->" % _expr
        else:
            _expr = "(%s)" % _expr

        if isinstance(out_struct["fields"], list):
            if count > 1:
                _arr = self._duplicate_as_array(_expr, out_struct["fields"][0], count)
                out_struct["fields"] = _arr["fields"]
                out_struct["size"] = _arr["size"]
            else:
                out_struct = self._duplicate_as_array(_expr, out_struct, 1)
        elif isinstance(out_struct["fields"], dict):
            out_struct = self._duplicate_as_array(_expr, out_struct, count)
        # else:
        #     raise NotImplementedError(out_struct["fields"])

        return out_struct

    def deref_function_pointer(self, struct: ViewStruct, io_stream: Stream, count: int, virtual_base=0) -> ViewStruct | None:
        if not struct["is_funcptr"]:
            raise ValueError("Can only deref a function pointer")
        addr = struct["value"] or _read_value(struct, io_stream)
        if addr == 0:
            return
        name = self._pdb.get_refname_from_offset(addr - virtual_base)
        if name is None:
            return

        y = struct.copy()
        y["levelname"] = name
        y["type"] = struct["type"][:-2] if struct["type"].endswith(" *") else ""
        y["is_pointer"] = False
        y["fields"] = None
        y["address"] = addr

        if count > 1:
            out_struct = self._duplicate_as_array("", y, count)
            for child in out_struct["fields"]:
                io_stream.seek(child["address"])
                val = int.from_bytes(io_stream.read(child["size"]), "little")
                child["value"] = val
                child["levelname"] = self._pdb.get_refname_from_offset(val - virtual_base) or "NULL"
            return out_struct
        else:
            x = struct.copy()
            x["fields"] = {
                name: y,
            }
            return x

    # for scripting

    def _insert_fptr_name(self, s: ViewStruct, virtual_base: int=0, io_stream=None):
        if io_stream is None:
            return
        if s["is_funcptr"]:
            val = _read_value(s, io_stream)
            s["levelname"] = self._pdb.get_refname_from_offset(val - virtual_base) or ""
        if isinstance(s["fields"], dict):
            for c in s["fields"].values():
                self._insert_fptr_name(c, virtual_base)
        elif isinstance(s["fields"], list):
            for c in s["fields"]:
                self._insert_fptr_name(c, virtual_base)
    
    def query_cstruct(self, expr: str, virtual_base: int=0, io_stream=None) -> CStruct:
        s = self.query_struct(expr, virtual_base, io_stream)
        self._insert_fptr_name(s, virtual_base, io_stream)
        return CStruct(s, io_stream)

    def deref_cstruct(self, cs: CStruct, count=1, virtual_base: int=0):
        s = self.deref_struct(cs._record, cs._stream, count)
        self._insert_fptr_name(s, virtual_base, cs._stream)
        return CStruct(s, cs._stream)
