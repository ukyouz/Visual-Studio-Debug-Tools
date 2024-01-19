import io
import os
import sys
from collections import Counter
from dataclasses import dataclass
from dataclasses import field
from typing import Optional
from typing import Type

from ctrl.qtapp import AppCtrl
from ctrl.qtapp import ClsType
from ctrl.qtapp import HistoryMenu
from ctrl.qtapp import MenuAction
from ctrl.qtapp import Plugin
from ctrl.qtapp import PluginNotLoaded
from ctrl.qtapp import set_app_title
from helper import qtmodel
from modules.winkernel import ProcessDebugger
from plugins import loadpdb


class DebuggerStream:
    def __init__(self, proc: ProcessDebugger) -> None:
        self._proc = proc
        self._offset = 0

    def seek(self, offset, pos=os.SEEK_SET):
        if pos == os.SEEK_END:
            raise NotImplementedError()
        if pos == os.SEEK_SET:
            self._offset = offset
        elif pos == os.SEEK_CUR:
            self._offset += offset
        else:
            raise NotImplementedError()

    def read(self, size: int) -> bytes:
        return self._proc.read_memory(self._offset, size)


class Debugger(Plugin):

    def attach_process(self, name):
        self.proc = ProcessDebugger.from_process_name(name)
        # self.menu("Debugger").setEnabled(True)

    def pause_process(self):
        if self.proc is None:
            return

    def get_memory_stream(self):
        return DebuggerStream(self.proc)

