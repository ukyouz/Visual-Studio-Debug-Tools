from minidump.minidumpfile import MinidumpFile


class MdumpFile(MinidumpFile):
    @classmethod
    def fromfile(cls, filename: str):
        mf = cls()
        mf.filename = filename
        mf.file_handle = open(filename, 'rb')
        mf._parse()
        return mf

    def read_memory(self, vaddr: int, byte_sz: int) -> bytes:
        if self.file_handle is None:
            raise ValueError("No minidump file is loaded.")
        if self.memory_segments_64:
            for seg in self.memory_segments_64.memory_segments:
                if seg.start_file_address is None:
                    continue
                if seg.start_virtual_address is None:
                    continue
                if vaddr < seg.start_virtual_address:
                    continue
                if seg.end_virtual_address is None:
                    continue
                if seg.end_virtual_address < vaddr + byte_sz:
                    continue
                self.file_handle.seek(seg.start_file_address + vaddr - seg.start_virtual_address)
                return self.file_handle.read(byte_sz)
        raise RuntimeError("Memory not found for {:#x} +{}".format(vaddr, byte_sz))

    def write_memory(self, vaddr: int, buf: bytes) -> int:
        raise RuntimeError("Not support to write memory to dump file.")