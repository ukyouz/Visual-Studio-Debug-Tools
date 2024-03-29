import os

from modules.winappdbg.winappdbg import Debug
from modules.winappdbg.winappdbg import Process
from modules.winappdbg.winappdbg import win32
from modules.winappdbg.winappdbg.win32 import dbghelp
from modules.winappdbg.winappdbg.win32 import kernel32


class UsageError(Exception):
    """ raise when error usage """


class ProcessDebugger:
    def __init__(self, pid: int):
        self.proc = Process(pid)
        self._pdb_loaded = False

    @classmethod
    def from_process_name(cls, name: str):
        dbg = Debug()
        dbg.system.scan_processes()
        procs = dbg.system.find_processes_by_filename(name)
        if len(procs) == 0:
            raise ValueError("Process name not found: %r" % name)
        if len(procs) > 1:
            raise ValueError("Multiple processes found: %r" % name)

        p, name = procs[0]
        return cls(p.get_pid())

    @staticmethod
    def list_processes():
        dbg = Debug()
        return dbg.system.iter_processes()

    def load_pdb(self, pdb: str, load_addr: int):
        self._pdb_loaded = True
        handle = self.proc.get_handle(win32.PROCESS_VM_READ | win32.PROCESS_QUERY_INFORMATION)
        dbghelp.SymInitialize(handle)
        sz = os.path.getsize(pdb)
        dbghelp.SymLoadModule64(handle, 0, pdb.encode(), None, load_addr, sz)

    def get_symbol(self, name: str):
        if not self._pdb_loaded:
            raise UsageError("You shall load a pdb file first using load_pdb(fname, addr) method.")
        handle = self.proc.get_handle(win32.PROCESS_VM_READ | win32.PROCESS_QUERY_INFORMATION)
        return dbghelp.SymFromName(handle, name.encode())

    def read_memory(self, addr: int, size: int):
        dat = self.proc.read(addr, size)
        return dat

    def write_memory(self, addr: int, buf: bytes) -> int:
        try:
            self.proc.write(addr, buf)
            return len(buf)
        except:
            return 0