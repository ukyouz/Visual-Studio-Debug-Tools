import logging
import os
import re
from typing import Any
from typing import NoReturn

from tree_sitter import Language
from tree_sitter import Node
from tree_sitter import Parser
import tree_sitter_c as tsc

from modules.pdbparser.pdbparser import pdb
from modules.utils.myfunc import BITMASK
from modules.utils.typ import Stream

logger = logging.getLogger(__name__)


REG_STRUCT = re.compile(r"(?:struct\s*)?(?P<STRUCT>[^* ]+)\s*(?P<STAR>\*)?")


class InvalidExpression(Exception):
    """invalid expr"""


class ArgumentError(Exception):
    """argument error"""


def _calc_val(fileio: Stream, item: pdb.StructRecord) -> Any:
    if item["value"] is not None:
        return item["value"]
    if fileio is None:
        raise ArgumentError("You shall provide a io_stream")
    base = item["address"]
    size = item["size"]
    boff = item["bitoff"]
    bsize = item["bitsize"]

    fileio.seek(base)
    int_with_sign = item.get("has_sign", False) and not item.get("is_real", False)
    val = int.from_bytes(fileio.read(size), "little", signed=int_with_sign)
    if boff is not None and bsize is not None:
        val = (val >> boff) & BITMASK(bsize)
    item["value"] = val

    return val


def get_syntax_tree(src: str):
    parser = Parser(Language(tsc.language()))
    tree = parser.parse(src.encode())
    return tree


def deref_pointer(p: pdb.PDB7, io_stream: Stream | None, struct: pdb.StructRecord, index: int | None, ref_expr=b"", allow_null_pointer=False) -> pdb.StructRecord:
    """
    index:
        None: deref by notation x-> or *(x)
        int: deref by x[n]
    """

    if struct["value"] is None or struct["value"] == 0:
        try:
            _addr = _calc_val(io_stream, struct)
        except OSError as e:
            raise OSError("%s: 0x%x, %r" % (str(e), struct["address"], ref_expr))
    else:
        _addr = struct["value"]

    if _addr == 0 and not allow_null_pointer:
        raise InvalidExpression("Try to access pointer at address 0 for %r" % ref_expr)

    if not struct.get("pointer_literal", False):
        try:
            struct = p.tpi_stream.deref_pointer(struct["lf"], _addr, recursive=False)
        except ValueError as e:
            raise InvalidExpression("%s at %r" % (e, ref_expr))
        except NotImplementedError as e:
            raise InvalidExpression("Fail to deref: %r" % ref_expr)

    assert isinstance(_addr, int), repr(_addr)
    out_struct = p.tpi_stream.form_structs(struct["lf"], _addr, recursive=False)
    if index is not None:
        out_struct["levelname"] = "[%d]" % index
        out_struct["address"] += out_struct["size"] * index
        s = pdb.new_struct(
            type="LF_ARRAY",
            address=_addr,
            fields=[None] * (index + 1),
        )
        s["fields"][index] = out_struct
        out_struct = s
    elif out_struct["fields"] is None:
        s = struct.copy()
        s["fields"] = [out_struct]
        s["_do_not_parse_again"] = [out_struct]
        out_struct = s

    return out_struct


def query_struct_from_expr(p: pdb.PDB7, expr: str, virt_base=0, io_stream=None, allow_null_pointer=False) -> pdb.StructRecord:
    if p is None:
        return pdb.new_struct()
    tree = get_syntax_tree(expr)

    def _get_value_of(x: pdb.StructRecord | int) -> int:
        if isinstance(x, dict):
            return _calc_val(io_stream, x)
        else:
            return x

    def _walk_syntax_node(node: Node) -> pdb.StructRecord | int:
        childs = node.children
        match node.type:
            case "translation_unit":
                assert childs != [], "Translation Unit is empty."
                assert len(childs) == 1 or childs[1].type == ";", "Translation Unit not support: %r" % node.text
                return _walk_syntax_node(childs[0])
            case "expression_statement":
                assert len(childs) < 2 or childs[1].type == ";", "Expression/Statement not support: %r" % node.text
                return _walk_syntax_node(childs[0])
            case "ERROR":
                assert len(childs) == 1, "Invalid syntax: %r" % node.text
                return _walk_syntax_node(childs[0])
            case "parenthesized_expression":
                # assert childs[0].type == '(' and childs[2].type == ')', "Invalid syntax: %r" % node.text
                assert len(childs) == 3, "Invalid syntax: %r" % node.text
                return _walk_syntax_node(childs[1])
            case "cast_expression":
                # assert childs[0].type == '(' and childs[2].type == ')'
                structname = childs[1].text.decode()
                match = REG_STRUCT.match(structname)
                if match is None:
                    raise InvalidExpression("Bad struct casting: b%r" % structname)
                if match["STAR"] is not None:
                    # ie: xxx_def *
                    lf, _ = p.get_lf_from_name(match.group("STRUCT"))
                    pointer_literal = True
                else:
                    # ie: xxx_def_ptr
                    lf, _ = p.get_lf_from_name(structname)
                    pointer_literal = False
                if lf is None:
                    raise InvalidExpression("Bad struct casting: b%r" % structname)

                address = _get_value_of(_walk_syntax_node(childs[3]))
                struct = pdb.new_struct(
                    type=structname,
                    value=address,
                    address=address,
                    size=p.tpi_stream.ARCH_PTR_SIZE,
                    is_pointer=True,
                    lf=lf,
                )
                struct["pointer_literal"] = pointer_literal
                return struct
            case "pointer_expression":
                # assert childs[0].type in {"&", "*"}
                struct = _walk_syntax_node(childs[1])
                if childs[0].type == "&":
                    if isinstance(struct, dict):
                        return struct["address"]
                    elif isinstance(struct, int):
                        return struct
                    else:
                        assert False, repr(node)
                elif childs[0].type == "*":
                    return deref_pointer(p, io_stream, struct, None, childs[1].text, allow_null_pointer)
                else:
                    assert False, repr(node)
            case "field_expression":
                # foo.bar
                # foo->bar
                struct = _walk_syntax_node(childs[0])
                assert isinstance(struct, dict), "Not a struct: %r" % childs[0].text
                notation = childs[1].type
                field = childs[2].text.decode()
                if notation == ".":
                    assert struct["fields"] is not None, "Notation error for pointer: b'%s%s'" % (notation, field)
                    assert not isinstance(struct["fields"], list), "Notation error for array: b'%s%s'" % (notation, field)
                    sub_struct = struct["fields"][field]
                elif notation == "->":
                    struct = deref_pointer(p, io_stream, struct, None, childs[0].text, allow_null_pointer)
                    assert isinstance(struct["fields"], dict), "Member not exists: b%r" % field
                    sub_struct = struct["fields"][field]
                else:
                    raise NotImplementedError(node.text)
                return p.tpi_stream.form_structs(
                    sub_struct["lf"],
                    addr=sub_struct["address"],
                    recursive=False
                )
            case "subscript_expression":
                # foo[0]
                # assert childs[1].type == '[' and childs[3].type == ']'
                struct = _walk_syntax_node(childs[0])
                assert isinstance(struct, dict), "Fail to get index from: %r" % childs[0].text
                index = _get_value_of(_walk_syntax_node(childs[2]))
                if struct["fields"] is None:
                    struct = deref_pointer(p, io_stream, struct, index, childs[0].text, allow_null_pointer)
                assert isinstance(struct["fields"], list), "Shall be an array or pointer: %r" % childs[0]
                try:
                    sub_struct = struct["fields"][index]
                except IndexError:
                    raise InvalidExpression("Index out of range: b'[%d]'" % index)
                return p.tpi_stream.form_structs(
                    sub_struct["lf"],
                    sub_struct["address"],
                    recursive=False,
                )
            case "identifier":
                structname = node.text.decode()
                lf, offset = p.get_lf_from_name(structname)
                assert lf is not None, "Identifier not found: %r" % structname
                out_struct = p.tpi_stream.form_structs(lf, virt_base + offset, recursive=False)
                return out_struct
            case "type_identifier":
                structname = node.text.decode()
                lf, offset = p.get_lf_from_name(structname)
                assert lf is not None, "Identifier not found: %r" % structname
                out_struct = p.tpi_stream.form_structs(lf, virt_base + offset, recursive=False)
                return out_struct
            case "number_literal":
                return eval(node.text.decode())
            case "sizeof_expression":
                struct = _walk_syntax_node(childs[1])
                if isinstance(struct, int):
                    return p.tpi_stream.ARCH_PTR_SIZE
                elif isinstance(struct, dict):
                    return struct["size"]
                else:
                    raise InvalidExpression("Fail to calculate: %r" % node.text)
            case "binary_expression":
                lhs = _walk_syntax_node(childs[0])
                operator = childs[1].type
                rhs = _walk_syntax_node(childs[2])
                if isinstance(lhs, dict) and lhs["is_pointer"] and isinstance(rhs, int):
                    # shift pointer by count
                    if operator not in "+-":
                        raise InvalidExpression("Invalid pointer movement: %r" % node.text)
                    deref_struct = deref_pointer(p, io_stream, lhs, None, childs[0].text, allow_null_pointer)
                    lhs["address"] = _get_value_of(lhs) + deref_struct["size"] * rhs * (-1 if operator == "-" else 1)
                    return lhs
                elif isinstance(lhs, dict) and isinstance(lhs["fields"], list) and isinstance(rhs, int):
                    # shift array head by count
                    if operator not in "+-":
                        raise InvalidExpression("Invalid array movement: %r" % node.text)
                    lhs = lhs["fields"][0]
                    lhs["address"] += lhs["size"] * rhs * (-1 if operator == "-" else 1)
                    lhs["levelname"] = "[%d]" % rhs
                    return lhs
                else:
                    left = _get_value_of(lhs)
                    right = _get_value_of(rhs)
                    match operator:
                        case "&&":
                            return int(left and right)
                        case "||":
                            return int(left or right)
                        case _:
                            return eval("int(%d %s %d)" % (left, operator, right))
            case "update_expression":
                # x ++
                # x --
                lhs = _walk_syntax_node(childs[0])
                base_value = _get_value_of(lhs)
                operator = childs[1].type
                match operator:
                    case "--":
                        if isinstance(lhs, dict) and lhs["is_pointer"]:
                            deref_struct = deref_pointer(p, io_stream, lhs, None, childs[0].text, allow_null_pointer)
                            lhs["address"] = _get_value_of(lhs) - deref_struct["size"]
                            return lhs
                        else:
                            return base_value - 1
                    case "++":
                        if isinstance(lhs, dict) and lhs["is_pointer"]:
                            deref_struct = deref_pointer(p, io_stream, lhs, None, childs[0].text, allow_null_pointer)
                            lhs["address"] = _get_value_of(lhs) + deref_struct["size"]
                            return lhs
                        else:
                            return base_value + 1
                    case _:
                        raise InvalidExpression("Not support update expression: %r" % operator)
            case "conditional_expression":
                # x ? 1 : 2
                assert childs[1].type == "?" and childs[3].type == ":", "Invalid syntax: " % node.text
                cond = _get_value_of(_walk_syntax_node(childs[0]))
                if bool(cond):
                    return _walk_syntax_node(childs[2])
                else:
                    return _walk_syntax_node(childs[4])
            case "offsetof_expression":
                # offset( type_descriptor, field_identifier )
                structname = childs[2].text.decode()
                member = childs[4].text.decode()
                match = REG_STRUCT.match(structname)
                assert match is not None, "Bad struct descriptor: b%r" % structname

                lf, _ = p.get_lf_from_name(match.group("STRUCT"))
                assert lf is not None, "Bad struct: b%r" % structname

                struct = p.tpi_stream.form_structs(lf, 0, recursive=False)
                if isinstance(struct, dict):
                    assert struct["fields"] is not None, "Struct b%r has no member" % (structname)
                    assert member in struct["fields"], "Member b%r not found in b%r" % (member, structname)
                    if isinstance(struct["fields"], dict):
                        return struct["fields"][member]["address"]
                    else:
                        raise NotImplementedError(struct["fields"])
                else:
                    raise NotImplementedError(struct)

            case "macro_type_specifier":
                raise InvalidExpression("Not support macro yet: %r" % node.text)
            case "call_expression":
                raise InvalidExpression("Not support function call yet: %r" % node.text)
            case "assignment_expression":
                raise InvalidExpression("Not support assignment yet: %r" % node.text)
            case _:
                raise InvalidExpression("Syntax not support: %r" % node)

    try:
        struct = _walk_syntax_node(tree.root_node)
    except AssertionError as e:
        raise InvalidExpression(e)
    except KeyError as e:
        raise InvalidExpression(repr(e))
    except ArgumentError as e:
        raise InvalidExpression("You shall provide a io_stream for the expression: %r" % expr)

    if isinstance(struct, dict):
        # struct result
        if not struct.get("pointer_literal", False) and not struct.get("_do_not_parse_again", False):
            out_struct = p.tpi_stream.form_structs(struct["lf"], addr=struct["address"])
        else:
            out_struct = struct
    elif isinstance(struct, int):
        # numeric result
        out_struct = pdb.new_struct(value=struct)
    else:
        raise NotImplementedError(expr)

    return out_struct


if __name__ == "__main__":
    get_syntax_tree("A.a[1][2]")
