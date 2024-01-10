# Python 2 and 3

from construct import Bytes
from construct import Container
from construct import CString
from construct import GreedyRange
from construct import Int8ul
from construct import Int16ul
from construct import Int32ul
from construct import ListContainer
from construct import PascalString
from construct import RestreamData
from construct import Struct
from construct import Switch

DATA_V2 = 0x1009
DATA_V3 = 0x110E


gsym = Struct(
    "leafKind" / Int16ul,
    "data" / Switch(
        lambda ctx: ctx.leafKind, {
            DATA_V3: Struct(
                "symtype" / Int32ul,
                "offset" / Int32ul,
                "section" / Int16ul,
                "name" / CString(encoding = "utf8"),
            ),
            DATA_V2: Struct(
                "symtype" / Int32ul,
                "offset" / Int32ul,
                "section" / Int16ul,
                "name" / PascalString(lengthfield = "length" / Int8ul, encoding = "utf8"),
            ),
        }))

GlobalsData = GreedyRange(
    Struct(
        "length" / Int16ul,
        "symbol" / RestreamData(Bytes(lambda ctx: ctx.length), gsym),
    ))


def parse(data):
    con = GlobalsData.parse(data)
    return merge_structures(con)


def parse_stream(stream):
    con = GlobalsData.parse_stream(stream)
    return merge_structures(con)


def merge_structures(con):
    new_cons = []
    for sym in con:
        sym_dict = {'length': sym.length, 'leafKind': sym.symbol.leafKind}
        if sym.symbol.data:
            sym_dict.update({
                'symtype': sym.symbol.data.symtype,
                'offset': sym.symbol.data.offset,
                'section': sym.symbol.data.section,
                'name': sym.symbol.data.name
            })
        new_cons.append(Container(sym_dict))
    result = ListContainer(new_cons)
    return result
