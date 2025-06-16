import os
import io

from ctrl.qtapp import Plugin
from modules.winkernel import ProcessDebugger


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


class CachedStream:
    def __init__(self, proc: ProcessDebugger | None, buf: io.BytesIO, addr: int) -> None:
        self._proc = proc
        self._buf = buf
        self._addr = addr

    def seek(self, offset, pos=os.SEEK_SET) -> int:
        if pos == os.SEEK_SET:
            self._buf.seek(offset - self._addr, pos) 
        else:
            self._buf.seek(offset, pos)
        
        return self._addr + self._buf.tell()

    def read(self, size: int) -> bytes:
        if self._proc is None:
            return bytes()
        return self._buf.read(size)

    def write(self, buf: bytes) -> int:
        if self._proc is None:
            return 0
        addr = self._addr + self._buf.tell()
        return self._proc.write_memory(addr, buf)

    def tell(self) -> int:
        return self._addr + self._buf.tell()


class ProcessNotConnected(Exception):
    ...


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

    def get_memory_stream(self) -> DebuggerStream:
        return DebuggerStream(self.pd)

    def get_cached_stream(self, addr: int, size: int) -> CachedStream:
        if self.pd:
            try:
                bin = self.pd.read_memory(addr, size)
            except:
                buf = io.BytesIO(bytes(size))
            else:
                buf = io.BytesIO(bin)
        else:
            buf = io.BytesIO(bytes(size))
        return CachedStream(self.pd, buf, addr)

    def get_virtual_base(self) -> int:
        if self.pd is None:
            raise ProcessNotConnected("No process is connected.")
        return self.pd.proc.get_main_module().get_base()

