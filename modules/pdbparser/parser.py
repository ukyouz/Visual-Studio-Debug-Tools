import io
import struct
from contextlib import suppress
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from functools import cached_property
from io import BytesIO
from typing import TypedDict

from construct import Array
from construct import Bytes
from construct import Container
from construct import CString
from construct import GreedyRange
from construct import Int16ul
from construct import Int32ul
from construct import Padding
from construct import Struct

from . import tpi

_strarray = "names" / GreedyRange(CString(encoding = "utf8"))


# ref: https://llvm.org/docs/PDB/MsfFile.html#file-layout

_PDB7_SIGNATURE = b"Microsoft C/C++ MSF 7.00\r\n\x1ADS\0\0\0"

StructPdbHeader = Struct(
    "signature" / Bytes(len(_PDB7_SIGNATURE)),
    "blockSize" / Int32ul,
    "freeBlockMapCount" / Int32ul,
    "numBlocks" / Int32ul,
    "numDirectoryBytes" / Int32ul,
    "Unknown" / Int32ul,
    # pointer array to each Stream Directory
    "BlockMapAddr" / Int32ul,
)

@dataclass
class Stream:
    byte_sz: int
    page_sz: int
    pages: list[int]
    _sHeader: Struct = field(default_factory=Struct)

    def getdata(self, fp) -> bytes:
        data = BytesIO()
        for p in self.pages:
            fp.seek(p * self.page_sz)
            data.write(fp.read(self.page_sz))
        return data.getbuffer()

    def getbodydata(self, fp) -> bytes:
        hdr_cls = getattr(self.__class__, "_sHeader", self._sHeader)
        hdr_offset = hdr_cls.sizeof()
        return self.getdata(fp)[hdr_offset:]

    def load_header(self, fp):
        data = self.getdata(fp)
        hdr_cls = getattr(self.__class__, "_sHeader", self._sHeader)
        self.header = hdr_cls.parse(data)

    def load_body(self, fp):
        """ heavy loading operations goes here """


class OldDirectory(Stream):
    ...


class PdbStream(Stream):
    _sHeader = Struct(
        "version" / Int32ul,
        "signature" / Int32ul,
        "age" / Int32ul,
        "guid" / Bytes(16),
        "charCnt" / Int32ul,
    )

    def load_data(self, fp):
        self.timestamp = datetime.fromtimestamp(self.header.signature)

        data = self.getbodydata(fp)
        self.strings = _strarray.parse(data[: self.header.charCnt])


class StructRecord(TypedDict):
    levelname: str
    val: int
    type: str
    base: int
    size: int
    bitoff: int
    bitsize: int
    fields: list


def new_struct(**kwargs):
    s = StructRecord(
        levelname="",
        value=0,
        type="",
        base=0,
        size=0,
        bitoff=None,
        bitsize=None,
        fields=None,
    )
    s.update(**kwargs)
    return s


class TpiStream(Stream):
    _sHeader = Struct(
        "version" / Int32ul,
        "headerSize" / Int32ul,
        "typeIndexBegin" / Int32ul,
        "typeIndexEnd" / Int32ul,
        "typeRecordBytes" / Int32ul,

        "sn" / Int16ul,
        Padding(2),
        "hashKey" / Int32ul,
        "numHashBuckets" / Int32ul,

        "hashValueBufferOffset" / Int32ul,
        "hashValueBufferLength" / Int32ul,

        "indexOffsetBufferOffset" / Int32ul,
        "indexOffsetBufferLength" / Int32ul,

        "hashAdjBufferOffset" / Int32ul,
        "hashAdjBufferLength" / Int32ul,
    )

    def structs(self) -> dict[str, int]:
        """ return dict of {structname: idx} """
        types = getattr(self, "types", {})
        return {
            t.data.name: idx
            for idx, t in types.items()
            if t.leafKind in {
                tpi.eLeafKind.LF_STRUCTURE,
                tpi.eLeafKind.LF_STRUCTURE_ST,
                tpi.eLeafKind.LF_UNION,
                tpi.eLeafKind.LF_UNION_ST,
            }
        }

    def _resolve_refs(self, lf, inside_fields: bool=False):
        ref_fields = tpi.FieldsRefAttrs if inside_fields else tpi.TypRefAttrs

        for attr in ref_fields.get(lf.leafKind, []):
            ref = lf[attr]
            if isinstance(ref, int):
                if ref < self.header.typeIndexBegin:
                    try:
                        setattr(lf, attr + "Ref", tpi.eBaseTypes[ref])
                    except KeyError:
                        print(hex(ref))
                elif ref >= self.header.typeIndexBegin:
                    with suppress(KeyError):
                        setattr(lf, attr + "Ref", self.types[ref])
            elif isinstance(ref, list):
                raise NotImplemented(ref)

    def _foward_refs(self, lf, fwdref_map, inside_fields: bool=False):
        ref_fields = tpi.FieldsRefAttrs if inside_fields else tpi.TypRefAttrs

        for attr in ref_fields.get(lf.leafKind, []):
            ref = lf[attr]
            if isinstance(ref, int):
                if ref < self.header.typeIndexBegin:
                    with suppress(KeyError):
                        setattr(lf, attr, fwdref_map[ref])
                elif ref >= self.header.typeIndexBegin:
                    with suppress(KeyError):
                        setattr(lf, attr, fwdref_map[ref])
            elif isinstance(ref, list):
                raise NotImplemented(ref)

    def _insert_field_of_raw(self, t_data):
        if not hasattr(t_data, "_raw"):
            return
        if t_data._raw._data0 < int(tpi.eLeafKind.LF_CHAR):
            t_data[t_data._raw._raw_attr] = t_data._raw._data0
            t_data["name"] = t_data._raw._data1
        else:
            t_data[t_data._raw._raw_attr] = t_data._raw._data1.value
            t_data["name"] = t_data._raw._data1.name

    def _flatten_leaf(self, lf):
        """ insert leafKind to data attribute, and return attribute as a new leaf """
        if lf.data is None:
            lf.data = Container()
        lf.data.leafKind = lf.leafKind
        return lf.data

    def load_body(self, fp):
        data = self.getbodydata(fp)
        arr = Array(
            self.header.typeIndexEnd - self.header.typeIndexBegin,
            tpi.sTypType
        )
        types = arr.parse(data)
        type_dict = {}
        for idx, t in zip(
            range(self.header.typeIndexBegin, self.header.typeIndexEnd),
            types,
        ):
            new_t = self._flatten_leaf(t)
            if new_t.leafKind is tpi.eLeafKind.LF_FIELDLIST:
                for i, f in enumerate(new_t.fields):
                    new_t.fields[i] = self._flatten_leaf(f)
            type_dict[idx] = new_t

        # fix values
        for t in type_dict.values():
            if t.leafKind is tpi.eLeafKind.LF_FIELDLIST:
                for f in t.fields:
                    self._insert_field_of_raw(f)
            else:
                self._insert_field_of_raw(t)
        self.types = type_dict

        ## eliminate fwdrefs
        # Get list of fwdrefs
        fwdrefs = {
            t.name: idx
            for idx, t in type_dict.items()
            if hasattr(t, "property") and t.property.fwdref
        }
        # Map them to the real type
        fwdrefs_map = {
            fwdrefs[t.name]: idx
            for idx, t in type_dict.items()
            if hasattr(t, "name") and hasattr(t, "property") and not t.property.fwdref and t.name in fwdrefs
        }
        # resolve fields
        for t in type_dict.values():
            if t.leafKind is tpi.eLeafKind.LF_FIELDLIST:
                for f in t.fields:
                    self._foward_refs(f, fwdrefs_map, inside_fields=True)
            else:
                self._foward_refs(t, fwdrefs_map, inside_fields=False)
        # Get rid of the resolved fwdrefs
        for k in fwdrefs_map.keys():
            del type_dict[k]

        # resolve fields
        for t in type_dict.values():
            if t.leafKind is tpi.eLeafKind.LF_FIELDLIST:
                for f in t.fields:
                    self._resolve_refs(f, inside_fields=True)
            else:
                self._resolve_refs(t, inside_fields=False)

        # test
        structs = {}
        for lf_idx, lf in type_dict.items():
            if lf.leafKind in {
                tpi.eLeafKind.LF_STRUCTURE,
                tpi.eLeafKind.LF_STRUCTURE_ST,
                tpi.eLeafKind.LF_UNION,
                tpi.eLeafKind.LF_UNION_ST,
            }:
                if lf.name.startswith("_") or lf.size == 0:
                    continue
                # print(lf_idx, lf.name)
                structs[lf.name] = lf
        self.structs = structs

    def form_structs(self, lf, base=0) -> StructRecord:
        if isinstance(lf, tpi.BasicType):
            return new_struct(
                levelname=lf.name,
                type = str(lf),
                base = base,
                size = lf.size,
            )
        elif lf.leafKind in {
            tpi.eLeafKind.LF_STRUCTURE,
            tpi.eLeafKind.LF_STRUCTURE_ST,
            tpi.eLeafKind.LF_UNION,
            tpi.eLeafKind.LF_UNION_ST,
        }:
            struct = new_struct(
                levelname="",
                type=lf.name,
                base = base,
                size = lf.size,
                fields={},
            )
            for member in lf.fieldsRef.fields:
                mem_struct = self.form_structs(member, base)
                if mem_struct is None:
                    continue
                mem_struct["levelname"] = member.name
                struct["fields"][member.name] = mem_struct
            return struct

        elif lf.leafKind == tpi.eLeafKind.LF_ARRAY:
            struct = new_struct(
                levelname = lf.name,
                type = str(lf.leafKind),
                base = base,
                size = lf.size,
                fields = [],
            )
            count = lf.size // lf.elemTypeRef.size
            for i in range(count):
                off = i * lf.elemTypeRef.size
                elem_s = self.form_structs(lf.elemTypeRef, base=base + off)
                elem_s["levelname"] = "[%d]" % i
                struct["fields"].append(elem_s)
            return struct

        elif lf.leafKind == tpi.eLeafKind.LF_MEMBER:
            struct = self.form_structs(lf.typeRef, base=base+lf.offset)
            struct["name"] = lf.name
            return struct

        elif lf.leafKind == tpi.eLeafKind.LF_NESTTYPE:
            # # anonymous?
            # struct = self.form_structs(lf.typeRef, base=base)
            # struct["name"] = lf.name
            # return struct
            return None

        elif lf.leafKind == tpi.eLeafKind.LF_BITFIELD:
            return new_struct(
                levelname = "",
                type = str(lf.leafKind),
                base=base,
                size=lf.baseTypeRef.size,
                bitoff=lf.position,
                bitsize=lf.length,
            )

        elif lf.leafKind == tpi.eLeafKind.LF_ENUM:
            return new_struct(
                levelname = lf.name,
                type = str(lf.leafKind),
                base = base,
                size = 4, #?
                fields = [], #?
            )

        elif lf.leafKind == tpi.eLeafKind.LF_POINTER:
            return new_struct(
                levelname = "",
                type = str(lf.leafKind),
                base = base,
                size = 4, #?
                fields = None,
            )

        else:
            raise NotImplementedError(lf)


class DbiStream(Stream):
    ...


STREAM_CLASSES = {
    # fix index
    0: OldDirectory,
    1: PdbStream,
    2: TpiStream,
    3: DbiStream,
}

U32_SZ = 4

def div_ceil(x, y):
    return (x + y - 1) // y


class PDB7:
    def __init__(self, fp):
        pdb_hdr_data = fp.read(StructPdbHeader.sizeof())
        pdb_hdr = StructPdbHeader.parse(pdb_hdr_data)
        self.header = pdb_hdr

        if pdb_hdr.signature != _PDB7_SIGNATURE:
            raise ValueError("Invalid signature for PDB version 7")

        """
        struct {
            uint32 numDirectoryBytes;
            uint32 blockSizes[numDirectoryBytes];
            uint32 blocks[numDirectoryBytes][];
        }
        """
        stream_dirs_pg_cnt = div_ceil(pdb_hdr.numDirectoryBytes, pdb_hdr.blockSize)
        fp.seek(pdb_hdr.BlockMapAddr * pdb_hdr.blockSize)
        root_dir_indice = struct.unpack(
            "<" + ("%dI" % stream_dirs_pg_cnt),
            fp.read(stream_dirs_pg_cnt * U32_SZ)
        )

        root_pages_data = io.BytesIO()
        for ind in root_dir_indice:
            fp.seek(ind * pdb_hdr.blockSize)
            root_pages_data.write(fp.read(pdb_hdr.blockSize))
        root_pages_data.seek(0)

        """"""""""""""""""

        num_streams, = struct.unpack("<I", root_pages_data.read(U32_SZ))
        streamSizes = struct.unpack(
            "<" + ("%sI" % num_streams),
            root_pages_data.read(num_streams * U32_SZ)
        )

        _streams = []
        for id, stream_sz in enumerate(streamSizes):
            stream_pg_cnt = div_ceil(stream_sz, pdb_hdr.blockSize)
            stream_pages = list(struct.unpack(
                "<" + ("%sI" % stream_pg_cnt),
                root_pages_data.read(stream_pg_cnt * U32_SZ)
            ))
            s = STREAM_CLASSES.get(id, Stream)(
                byte_sz=stream_sz,
                page_sz=pdb_hdr.blockSize,
                pages=stream_pages
            )
            _streams.append(s)

        for s in _streams:
            s.load_header(fp)
            s.load_body(fp)

        self.streams = _streams


def parse(filename) -> PDB7:
    "Open a PDB file and autodetect its version"
    with open(filename, 'rb') as f:
        sig = f.read(len(_PDB7_SIGNATURE))
        f.seek(0)
        if sig == _PDB7_SIGNATURE:
            pdb = PDB7(f)
            pdb.name = filename
            return pdb
        else:
           raise NotImplementedError(sig)


def _save_pdb(tpi, filename):
    import pickle
    with open(filename, "wb") as f:
        pickle.dump(tpi, f)


def load_pdbin(filename):
    import pickle
    with open(filename, "rb") as f:
        return pickle.load(f)


if __name__ == "__main__":
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("--pdb_file")
    p.add_argument("--out")
    args = p.parse_args()

    import time
    a = time.time()

    pdb = parse(args.pdb_file)
    # TPI = pdb.streams[2]

    print(time.time() - a)

    _save_pdb(pdb, args.out)