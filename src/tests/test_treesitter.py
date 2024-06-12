import os

import pytest

from modules.pdbparser.pdbparser import pdb
from modules.treesitter.expr_parser import InvalidExpression
from modules.treesitter.expr_parser import query_struct_from_expr


class TestStream:
    def __init__(self, value=0) -> None:
        self._val = value

    def seek(self, *args):
        return 0

    def read(self, size):
        return self._val.to_bytes(size, "little")


@pytest.fixture
def stream() -> TestStream:
    return TestStream(4)


@pytest.fixture(scope="module")
def p() -> pdb.PDB7:
    _p = pdb.parse(os.path.join(os.path.dirname(__file__), "data/Debug/ConsoleApplication1.pdb"))
    return _p


@pytest.mark.parametrize(
    "expr, err_msg",
    [
        ("((TextHolder)124)[4]", "Shall be a pointer type, got: 'TextHolder' at b'((TextHolder)124)'"),
        ("((yyy *)124)[4]", "Bad struct casting: b'yyy *'"),
        ("(0x123[2]", "Invalid syntax: b'(0x123[2]'"),
        ("1 || 3 ff", "Invalid syntax: b'1 || 3 ff'"),
        ("123[1]", "Fail to get index from: b'123'"),
        ("4 + (gA.attr -- 3)", "Invalid syntax: b'(gA.attr -- 3)'"),
        ("4 + (gA.attr -=2)", "Not support assignment yet: b'gA.attr -=2'"),
        ("gA.afunc->c", "Fail to deref: b'gA.afunc'"),
        ("gA.afunc.c", "Notation error for pointer: b'.c'"),
        ("gA.afunc[1]", "Fail to deref: b'gA.afunc'"),
        ("gA.b[gA.attr]", "KeyError('b')"),
        ("gA.s->szBuffer[gA.attr]", "Shall be a pointer type, got: 'TextHolder' at b'gA.s'"),
        ("gA.s.dwLen[1]", "Shall be a pointer type, got: 'T_LONG' at b'gA.s.dwLen'"),
        ("gC.bb", "Identifier not found: 'gC'"),
        ("get(gA, gB)", "Not support function call yet: b'get(gA, gB)'"),
        ("get(gA)", "Not support macro yet: b'get(gA)'"),
        ("g_Message.szBuffer[999]", "Index out of range: b'[999]'"),
        ("offsetof(ABC, arr)", "Bad struct: b'ABC'"),
        ("offsetof(A, axxx)", "Member b'axxx' not found in b'A'"),
    ]
)
def test_bad_exprs(stream: TestStream, p: pdb.PDB7, expr: str, err_msg: str):
    with pytest.raises(InvalidExpression) as excinfo:
        query_struct_from_expr(p, expr, io_stream=stream)
    assert err_msg == str(excinfo.value)


@pytest.mark.parametrize(
    "expr, expected_addr",
    [
        ("((struct A *)100)->attr", 100),
        ("(struct A *)100", 100),
        ("(struct A *)gA.pint", 12),
        ("*((struct A *)100)", 100),
        ("gA.x - 1", 12 - 4),
        ("gA.x + 1", 12 + 4),
        ("gB.s - 1", 12 - 260),
        ("gB.s + 1", 12 + 260),
        ("gB.s ++", 12 + 260),
        ("gB.s->szBuffer - 1", 11),
        ("gB.s->szBuffer + 1", 13),
        ("gB.s->szBuffer", 12),
        ("gB.s->szBuffer", 12),
    ]
)
def test_expr_addr(p: pdb.PDB7, expr: str, expected_addr: int):
    stream = TestStream(12)
    result = query_struct_from_expr(p, expr, io_stream=stream)
    assert isinstance(result, dict)
    assert result["address"] == expected_addr


@pytest.mark.parametrize(
    "expr",
    [
        # "((int *)a)[3]",
        "((struct B *)0)->s[3]",
        "((struct TextHolder *)0x123)[2]",
        "(struct A *)0",
        "*(((struct A *)0)->pint)",
        "((struct A *)0)->pint[0]",
        "*((struct B *)0)",
        "&(&gA)",
        "&(B.s->szBuffer)",
        "1 ? 4 : 9",
        "1 && 5",
        "4 + (gA.attr > 3)",
        "4 + (gA.attr--)",
        "A.arr[1][3]",
        "B.s->szBuffer[1]",
        "B",
        "BDef",
        "gA.s.szBuffer[gA.attr]",
        "gB.s[0].szBuffer",
        "gA",
        "sizeof(gA)",
        "(BDefPtr)100",
        "gA.x[0]",
        "offsetof(struct A, arr)",
        "offsetof(A, arr)",
    ]
)
def test_good_expr(stream: TestStream, p: pdb.PDB7, expr: str):
    result = query_struct_from_expr(p, expr, io_stream=stream, allow_null_pointer=True)
    assert isinstance(result, dict)