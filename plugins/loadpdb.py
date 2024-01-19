import io
import pickle
from pathlib import Path

from PyQt6 import QtWidgets

from ctrl.qtapp import MenuAction
from ctrl.qtapp import Plugin
from modules.pdbparser.pdbparser import pdb
from modules.pdbparser.pdbparser import picklepdb


class LoadPdb(Plugin):
    _pdb: pdb.PDB7

    def registerMenues(self) -> dict[str, list[MenuAction]]:
        return {
            "PDB": [
                {
                    "name": "Load PDB file...",
                    "command": "LoadPdbin",
                    # "shortcut": "",
                },
            ]
        }

    def registerCommands(self):
        if val := self.app.app_setting.value("LoadPdb/pdbin", ""):
            self.load_pdbin(val)
        return [
            ("LoadPdbin", self.load_pdbin),
        ]

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

    def _shift_addr(self, s: pdb.StructRecord, shift: int=0):
        s["address"] = s["address"] + shift
        if isinstance(s["fields"], dict):
            for c in s["fields"].values():
                self._shift_addr(c, shift)
        elif isinstance(s["fields"], list):
            for c in s["fields"]:
                self._shift_addr(c, shift)

    def parse_struct(self, structname: str, addr=0, count=1, add_dummy_root=False):
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
                levelname="%s[%d]" % (structname, count),
                type="LF_ARRAY",
                address=addr,
                size=count * s["size"],
                fields=childs,
            )
        else:
            s["levelname"] = structname
        if add_dummy_root:
            s = pdb.new_struct(
                fields=[s],
            )
        return s


class Test(Plugin):

    def registerCommands(self) -> list[tuple]:
        return [
            ("Test", self._test),
        ]

    def _test(self):
        pdb = self.app.plugin(LoadPdb)
        print(pdb._pdb)


