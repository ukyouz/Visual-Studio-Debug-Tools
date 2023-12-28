from PyQt6 import QtWidgets

from ctrl.qtapp import MenuAction
from ctrl.qtapp import Plugin
from modules.pdbparser import parser as pdbparser


class LoadPdb(Plugin):
    pdb: pdbparser.PDB7

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
        return [
            ("LoadPdbin", self._open_pdbin),
        ]

    def _open_pdbin(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.ctrl.view,
            caption="Open File",
            filter="Any (*.*)"
        )
        if filename:
            def _cb(_pdb):
                self.pdb = _pdb
                print(123)
                self.menu("PDB").setEnabled(True)

            self.menu("PDB").setEnabled(False)
            self.ctrl.exec_async(
                pdbparser.parse,
                filename,
                finished_cb=_cb,
            )
