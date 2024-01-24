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
    def __init__(self, proc: ProcessDebugger | None) -> None:
        self._proc = proc
        self._offset = 0

    def seek(self, offset, pos=os.SEEK_SET) -> int:
        if pos == os.SEEK_END:
            raise NotImplementedError()
        if pos == os.SEEK_SET:
            self._offset = offset
        elif pos == os.SEEK_CUR:
            self._offset += offset
        else:
            raise NotImplementedError()
        return self._offset

    def read(self, size: int) -> bytes:
        if self._proc is None:
            return bytes()
        return self._proc.read_memory(self._offset, size)

    def write(self, buf: bytes) -> int:
        if self._proc is None:
            return 0
        addr = self._offset
        return self._proc.write_memory(addr, buf)

    def tell(self) -> int:
        return self._offset


class Debugger(Plugin):

    def post_init(self):
        self.pd = None

    def attach_process(self, name):
        try:
            self.pd = ProcessDebugger.from_process_name(name)
            return None
        except Exception as e:
            return e

    def detach_process(self):
        if self.pd is None:
            return
        self.pd.proc.close_handle()

    def pause_process(self):
        if self.pd is None:
            return

    def get_memory_stream(self):
        return DebuggerStream(self.pd)

    def get_virtual_base(self):
        if self.pd is None:
            return None
        return self.pd.proc.get_main_module().get_base()

