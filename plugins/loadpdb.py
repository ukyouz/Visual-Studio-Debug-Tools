import io
from pathlib import Path

from PyQt6 import QtWidgets

from ctrl.qtapp import MenuAction
from ctrl.qtapp import Plugin
from modules.pdbparser import pdb
from modules.pdbparser import picklepdb


class LoadPdb(Plugin):
    pdb: pdb.PDB7

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
        if val := self.ctrl.app_setting.value("LoadPdb/pdbin", ""):
            self.load_pdbin(val)
        return [
            ("LoadPdbin", self.load_pdbin),
        ]

    def load_pdbin(self, filename=""):
        if not filename:
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                self.ctrl.view,
                caption="Open File",
                filter="Any (*.*)"
            )
        if filename:
            def _cb(_pdb):
                self.ctrl.app_setting.setValue("LoadPdb/pdbin", filename)
                self.pdb = _pdb
                print(_pdb)
                self.menu("PDB").setEnabled(True)

            self.menu("PDB").setEnabled(False)

            path = Path(filename)
            if path.suffix == ".pdbin":
                self.ctrl.exec_async(
                    picklepdb.load_pdbin,
                    filename,
                    finished_cb=_cb,
                )
            elif path.suffix == ".pdb":
                self.ctrl.exec_async(
                    pdb.parse,
                    filename,
                    finished_cb=_cb,
                )

    def parse_struct(self, structname: str, add_dummy_root=False):
        tpi = self.pdb.streams[2]
        try:
            lf = tpi.structs[structname]
        except KeyError:
            return pdb.new_struct()

        s = tpi.form_structs(lf)
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
        pdb = self.ctrl.plugin(LoadPdb)
        print(pdb.pdb)


