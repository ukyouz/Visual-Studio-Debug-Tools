import io
import pickle
from pathlib import Path

from PyQt6 import QtWidgets

from ctrl.qtapp import MenuAction
from ctrl.qtapp import Plugin
from modules.pdbparser.pdbparser import pdb
from modules.pdbparser.pdbparser import picklepdb


class DummyOmap:

    def remap(self, addr):
        return addr


class LoadPdb(Plugin):
    _pdb: pdb.PDB7

    def registerMenues(self) -> list[MenuAction]:
        return [
            {
                "name": "PDB",
                "submenus": [
                    {
                        "name": "Load PDB file...",
                        "command": "LoadPdbin",
                        # "shortcut": "",
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
            ("LoadPdbin", self.load_pdbin),
            ("ShowPdbStatus", self.show_status),
        ]

    def post_init(self):
        self._pdb_fname = ""
        if val := self.app.app_setting.value("LoadPdb/pdbin", ""):
            self.load_pdbin(val)

    def load_pdbin(self, filename=""):
        if not filename:
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                self.app,
                caption="Open File",
                filter="Any (*.*)"
            )
        if filename:
            def _cb(_pdb):
                self.app.app_setting.setValue("LoadPdb/pdbin", filename)
                self._pdb_fname = filename
                self._pdb = _pdb
                print(_pdb)
                self.menu("PDB").setEnabled(True)

            self.menu("PDB").setEnabled(False)

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

    def _shift_addr(self, s: pdb.StructRecord, shift: int=0):
        s["address"] = s["address"] + shift
        if isinstance(s["fields"], dict):
            for c in s["fields"].values():
                self._shift_addr(c, shift)
        elif isinstance(s["fields"], list):
            for c in s["fields"]:
                self._shift_addr(c, shift)

    def parse_struct(self, structname: str, expr: str="", addr=0, count=1, add_dummy_root=False):
        if expr == "":
            return pdb.new_struct()

        expr = expr or structname
        tpi = self._pdb.streams[2]
        try:
            lf = tpi.structs[structname]
        except KeyError:
            return pdb.new_struct()

        s = tpi.form_structs(lf, addr)
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
        else:
            s["levelname"] = expr
        if add_dummy_root:
            s = pdb.new_struct(
                fields=[s],
            )
        return s

    def query_expression(self, expr: str, virtual_base: int=0):
        tpi = self._pdb.streams[2]
        dbi = self._pdb.streams[3]
        glb = self._pdb.streams[dbi.header.symrecStream]

        if expr not in glb.s_gdata32:
            return None

        # remap global address
        try:
            sects = self._pdb.streams[dbi.dbgheader.snSectionHdrOrig].sections
            omap = self._pdb.streams[dbi.dbgheader.snOmapFromSrc]
        except AttributeError:
            sects = self._pdb.streams[dbi.dbgheader.snSectionHdr].sections
            omap = DummyOmap()
        glb_info = glb.s_gdata32[expr]
        section_offset = sects[glb_info.section - 1].VirtualAddress
        glb_addr = virtual_base + omap.remap(glb_info.offset + section_offset)

        struct = tpi.types[glb_info.typind].name
        return self.parse_struct(struct, expr, addr=glb_addr)


class Test(Plugin):

    def registerCommands(self) -> list[tuple]:
        return [
            ("Test", self._test),
        ]

    def _test(self):
        pdb = self.app.plugin(LoadPdb)
        print(pdb._pdb)


