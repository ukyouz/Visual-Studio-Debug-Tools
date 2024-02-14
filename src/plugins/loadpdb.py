import logging
import pickle
import re
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PyQt6 import QtWidgets

from ctrl.qtapp import MenuAction
from ctrl.qtapp import Plugin
from ctrl.WidgetPicklePdb import PicklePdb
from helper import qtmodel
from modules.pdbparser.pdbparser import pdb
from modules.pdbparser.pdbparser import picklepdb

logger = logging.getLogger(__name__)


class InvalidExpression(Exception):
    """invalid expr"""


class DummyOmap:
    def remap(self, addr):
        return addr


@dataclass
class CStruct:
    _record: pdb.StructRecord
    _stream: qtmodel.Stream

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
        item = self._record

        base = item["address"]
        size = item["size"]
        boff = item["bitoff"]
        bsize = item["bitsize"]

        self._stream.seek(base)
        val = int.from_bytes(self._stream.read(size), "little")
        if boff is not None and bsize is not None:
            val = (val >> boff) & qtmodel.bitmask(bsize)

        return val


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

    def _shift_addr(self, s: dict, shift: int=0):
        s["address"] = s["address"] + shift
        if isinstance(s["fields"], dict):
            for c in s["fields"].values():
                self._shift_addr(c, shift)
        elif isinstance(s["fields"], list):
            for c in s["fields"]:
                self._shift_addr(c, shift)

    def _add_expr(self, s, expr: str):
        s["expr"] = expr
        if isinstance(s["fields"], dict):
            if expr.endswith("->") or expr.endswith("."):
                notation = ""
            else:
                notation = "->" if s.get("is_pointer", False) else "."
            for c in s["fields"].values():
                self._add_expr(c, expr + notation + c["levelname"])
        elif isinstance(s["fields"], list):
            for c in s["fields"]:
                self._add_expr(c, expr + c["levelname"])

    def parse_struct(self, structname: str, expr: str="", addr=0, count=1, recursive=True, add_dummy_root=False) -> pdb.StructRecord:
        if structname == "":
            return pdb.new_struct()

        expr = expr or structname
        tpi = self._pdb.streams[2]
        dbi = self._pdb.streams[3]
        glb = self._pdb.streams[dbi.header.symrecStream]
        if structname in glb.s_udt:
            user_defined_type = glb.s_udt[structname]
            lf = tpi.get_type_lf(user_defined_type.typind)
        else:
            try:
                lf = tpi.structs[structname]
            except KeyError:
                raise InvalidExpression(structname)

        s = tpi.form_structs(lf, addr, recursive)
        if count > 1:
            s["levelname"] = "[0]"
            childs = [s]
            backup = pickle.dumps(s)
            for n in range(1, count):
                copied = pickle.loads(backup)
                copied["levelname"] = "[%d]" % n
                self._shift_addr(copied, n * s["size"])
                childs.append(copied)
            s = pdb.new_struct(
                levelname="%s[%d]" % (expr, count),
                type="LF_ARRAY",
                address=addr,
                size=count * s["size"],
                fields=childs,
            )
            self._add_expr(s, expr)
        else:
            s["levelname"] = expr
            self._add_expr(s, expr)
        if add_dummy_root:
            s = pdb.new_struct(
                fields=[s],
            )
        return s

    def _iter_fields(self, expr: str) -> Iterable[str | int]:
        _expr = expr.replace("->", ".")
        _expr = _expr.replace("[", ".")
        _expr = _expr.replace("]", ".")
        for f in _expr.split("."):
            if f == "":
                continue
            try:
                yield eval(f)
            except:
                yield f

    def _flatten_dict(self, s: dict, out: list):
        childs = s.get("fields", None)
        s["fields"] = None
        if isinstance(childs, dict):
            for c in childs.values():
                self._flatten_dict(c, out)
        elif isinstance(childs, list):
            for c in childs:
                self._flatten_dict(c, out)
        else:
            out.append(s)

    def parse_array(self, struct: str, expr: str="", addr=0, count=1):
        tpi = self._pdb.streams[2]

        subfields = list(self._iter_fields(struct))
        structname = subfields.pop(0)
        if not isinstance(structname, str):
            return

        has_childs = subfields == []
        out_struct = self.parse_struct(structname, expr, addr, recursive=has_childs)

        while subfields:
            f = subfields.pop(0)
            try:
                out_struct = out_struct["fields"][f]
            except:
                return

            if out_struct["is_pointer"]:
                return

            last_field = subfields == []
            lvlname = out_struct["levelname"]
            out_struct = tpi.form_structs(out_struct["lf"], addr=out_struct["address"], recursive=last_field)
            out_struct["levelname"] = lvlname
            self._add_expr(out_struct, "")

        if isinstance(out_struct["fields"], list):
            array = []
            for x in out_struct["fields"]:
                cut_pos = len(x["levelname"])
                row = []
                self._flatten_dict(x, row)
                for c in row:
                    c["expr"] = c["expr"][cut_pos:]
                array.append(row)
        else:
            backup = pickle.dumps(out_struct)

            array = []
            for n in range(count):
                copied = pickle.loads(backup)
                copied["levelname"] = "[%d]" % n
                self._shift_addr(copied, n * out_struct["size"])
                self._add_expr(copied, "")
                row = []
                self._flatten_dict(copied, row)
                array.append(row)

        return array

    def query_expression(self, expr: str, virtual_base: int=0, io_stream=None) -> dict | None:
        tpi = self._pdb.streams[2]
        dbi = self._pdb.streams[3]
        glb = self._pdb.streams[dbi.header.symrecStream]

        subfields = list(self._iter_fields(expr))
        top_expr = subfields.pop(0)
        if not isinstance(top_expr, str):
            return

        has_subfields = len(subfields)
        glb_info = None
        with suppress(KeyError):
            glb_info = glb.s_gdata32[top_expr]
        with suppress(KeyError):
            glb_info = glb.s_ldata32[top_expr]
        if glb_info:
            # remap global address
            try:
                sects = self._pdb.streams[dbi.dbgheader.snSectionHdrOrig].sections
                omap = self._pdb.streams[dbi.dbgheader.snOmapFromSrc]
            except AttributeError:
                sects = self._pdb.streams[dbi.dbgheader.snSectionHdr].sections
                omap = DummyOmap()
            section_offset = sects[glb_info.section - 1].VirtualAddress
            glb_addr = virtual_base + omap.remap(glb_info.offset + section_offset)

            lf = tpi.get_type_lf(glb_info.typind)
            out_struct = tpi.form_structs(lf, addr=glb_addr, recursive=not has_subfields)
            out_struct["levelname"] = top_expr
            self._add_expr(out_struct, top_expr)
        elif match := re.match(r"\((?P<STRUCT>.+)\*\s*\)(?P<ADDR>.+)", top_expr):
            # TODO: use C syntax parser for better commpatibility
            structname = match["STRUCT"].strip()
            addr = match["ADDR"]
            if structname not in tpi.structs:
                return
            try:
                glb_addr = eval(addr)
            except:
                return
            if top_expr[-1] != ")":
                top_expr = "(*(%s))" % top_expr
            else:
                top_expr = "*(%s)" % top_expr
            out_struct = self.parse_struct(structname, top_expr, addr=glb_addr, recursive=not has_subfields)
        else:
            return

        while subfields:
            f = subfields.pop(0)
            try:
                out_struct = out_struct["fields"][f]
            except:
                return

            last_field = subfields == []
            if not out_struct["is_pointer"]:
                lvlname = out_struct["levelname"]
                _expr = out_struct["expr"]
                out_struct = tpi.form_structs(out_struct["lf"], addr=out_struct["address"], recursive=last_field)
                out_struct["levelname"] = lvlname
                self._add_expr(out_struct, _expr)
            else:
                if io_stream is None:
                    return
                if last_field:
                    break
                io_stream.seek(out_struct["address"])
                addr = int.from_bytes(io_stream.read(out_struct["size"]), "little")
                count = f if isinstance(f, int) else 1
                notation = "->" if count == 1 else ""
                out_struct = self.parse_struct(
                    structname=out_struct["lf"].utypeRef.name,
                    expr=out_struct["expr"] + notation,
                    addr=addr,
                    count=count,
                    recursive=False,
                )

        out_struct["levelname"] = out_struct["expr"]
        return out_struct

    def deref_cstruct(self, cs: CStruct, addr: int=0, count=1) -> CStruct:
        # TODO: just use real c parser for derefence struct pointer
        item = cs._record
        if not hasattr(item["lf"], "utypeRef"):
            return None

        addr = addr or item.get("value", 0) or 0

        struct = item["lf"].utypeRef.name

        notation = "->" if count == 1 else ""
        expr = item.get("expr", "") + notation

        return CStruct(self.parse_struct(struct, expr, addr=addr, count=count), cs._stream)
