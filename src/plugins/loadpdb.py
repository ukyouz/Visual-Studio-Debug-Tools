import logging
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from typing import Self
from typing import TypedDict

from construct import Struct
from PyQt6 import QtWidgets

from ctrl.qtapp import MenuAction
from ctrl.qtapp import Plugin
from ctrl.WidgetPicklePdb import PicklePdb
from helper import qtmodel
from modules.pdbparser.pdbparser import pdb
from modules.pdbparser.pdbparser import picklepdb
from modules.treesitter.expr_parser import InvalidExpression
from modules.treesitter.expr_parser import query_struct_from_expr
from modules.utils.myfunc import BITMASK
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
    has_sign: bool
    lf: Struct | None

    expr: Optional[str]


def _read_value(item: pdb.StructRecord, stream: Stream) -> int:
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
    _record: pdb.StructRecord
    _stream: qtmodel.Stream | None

    def __getattr__(self, field: str):
        if not isinstance(self._record["fields"], dict):
            raise InvalidExpression("Field not found: %r" % field)
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


def _shift_addr(s: pdb.StructRecord, shift: int=0):
    s["address"] = s["address"] + shift
    if isinstance(s["fields"], dict):
        for c in s["fields"].values():
            _shift_addr(c, shift)
    elif isinstance(s["fields"], list):
        for c in s["fields"]:
            _shift_addr(c, shift)


def _add_expr(s: ViewStruct, expr: str):
    s["expr"] = expr
    if isinstance(s["fields"], dict):
        if expr.endswith("->") or expr.endswith("."):
            notation = ""
        else:
            notation = "->" if s.get("is_pointer", False) else "."
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


class LoadPdb(Plugin):
    _pdb: pdb.PDB7

    def registerMenues(self) -> list[MenuAction]:
        return [
            {
                "name": "PDB",
                "submenus": [
                    {
                        "name": "Generate PDB...",
                        "command": "ShowPicklePdb",
                        "icon": ":icon/images/vswin2019/Database_16x.svg",
                    },
                    {"name": "---",},
                    {
                        "name": "Show PDB status...",
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
        if val := self.app.app_setting.value("LoadPdb/pdbin", ""):
            self.load_pdbin(val)

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
            def _cb(_pdb):
                self.app.app_setting.setValue("LoadPdb/pdbin", filename)
                self._pdb_fname = filename
                self._pdb = _pdb
                self.app.statusBar().showMessage("Pdbin is Loaded.")

            path = Path(filename)
            if path.suffix == ".pdbin":
                self.app.exec_async(
                    picklepdb.load_pdbin,
                    filename,
                    finished_cb=_cb,
                )
            elif path.suffix == ".pdb":
                self.app.exec_async(
                    pdb.parse,
                    filename,
                    finished_cb=_cb,
                )
            self.app.statusBar().showMessage("Loading... %r" % filename)

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

    def parse_expr_to_struct(self, expr: str, addr=0, count=1, add_dummy_root=False) -> pdb.StructRecord:
        if expr == "":
            return pdb.new_struct()

        s = query_struct_from_expr(self._pdb, expr, addr)
        s = self._duplicate_as_array(expr, s, count)

        if add_dummy_root:
            s = pdb.new_struct(
                fields=[s],
            )
        return s

    def _tabulate_a_struct(self, struct: pdb.StructRecord, count: int) -> list[ViewStruct]:
        if isinstance(struct["fields"], list):
            array = []
            _take_count = len(struct["fields"]) if count == 0 else count
            for x in struct["fields"][: _take_count]:
                cut_pos = len(x["levelname"])
                row = []
                _flatten_dict(x, row)
                for c in row:
                    c["expr"] = c["expr"][cut_pos:]
                array.append(row)
        else:
            backup = pickle.dumps(struct)

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

    def parse_expr_to_table(self, expr: str, addr=0, count=1) -> list[ViewStruct]:
        out_struct = query_struct_from_expr(self._pdb, expr, addr)
        _add_expr(out_struct, "")
        array = self._tabulate_a_struct(out_struct, count)
        return array

    def query_struct(self, expr: str, virtual_base: int=0, io_stream=None) -> ViewStruct:
        struct = query_struct_from_expr(self._pdb, expr, virtual_base, io_stream)
        struct["levelname"] = expr
        _add_expr(struct, expr)
        return struct

    def deref_struct(self, struct: ViewStruct, io_stream: Stream, count=1) -> ViewStruct:
        if count == 0:
            raise ValueError("Deref count at least 1, got: %d" % count)
        _type = struct["type"]
        if _type.startswith("(") and _type.endswith(")"):
            _type = _type[1: -1]
        addr = struct["value"] or _read_value(struct, io_stream)
        expr = "*(({}){:#08x})".format(_type, addr)
        out_struct = query_struct_from_expr(self._pdb, expr, io_stream=io_stream)

        expr = struct.get("expr", "") or ""
        if count == 1:
            expr = "*(%s)" % expr
        out_struct = self._duplicate_as_array(expr, out_struct, count)

        return out_struct

    # for scripting

    def query_cstruct(self, expr: str, virtual_base: int=0, io_stream=None) -> CStruct:
        s = self.query_struct(expr, virtual_base, io_stream)
        return CStruct(s, io_stream)

    def deref_cstruct(self, cs: CStruct, count=1):
        s = self.deref_struct(cs._record, cs._stream, count)
        return CStruct(s, cs._stream)
