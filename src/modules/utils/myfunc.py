import math
import re
import struct
from functools import cache
from pathlib import Path


@cache
def BIT(bit: int) -> int:
    return 1 << bit


@cache
def BITMASK(bitcnt):
    return BIT(bitcnt) - 1


# https://stackoverflow.com/questions/7822956/how-to-convert-negative-integer-value-to-hex-in-python
def hex2(val: int, nbits: int, pad_zero=False) -> str:
    # return hex string in two's-complement format
    if pad_zero and val >= 0:
        nchar = math.ceil(nbits // 8) * 2
        return f"{{:#0{nchar + 2}x}}".format(val)
    else:
        return hex((val + BIT(nbits)) % BIT(nbits))


# https://stackoverflow.com/questions/30124608/convert-unsigned-integer-to-float-in-python
# https://stackoverflow.com/questions/8341395/what-is-a-subnormal-floating-point-number
def float_from_int(val: int, nbits: int) -> float:
    # TODO: support real64, real128
    # method 1
    if nbits <= 32:
        fp = struct.unpack("f", struct.pack("I", val))[0]
    else:
        fp = struct.unpack("d", struct.pack("Q", val))[0]

    # remove fractions under precision
    precision = len(str(fp)) - 2
    for pos in range(precision, 0, -1):
        check = float(f"{{:.{pos}f}}".format(fp))
        if int_from_float(check, nbits) != val:
            break
        if len(str(check)) < pos:
            # stop when the precision changes more than 3 digits
            break
        fp = check
    return fp


def float_from_ieee754(val: int) -> float:
    # method 2
    if val > 0xFFFFFFFF:
        raise NotImplementedError("Value too big: %09x" % val)
    sign = val >> 31
    exp = (val & 0x7F800000) >> 23
    frac = val & 0x007FFFFF
    if exp == 0 and frac == 0:
        return ((-1) ** sign) * 0.0
    if exp == 0xFF:
        if frac == 0:
            return ((-1) ** sign) * math.inf
        else:
            return math.nan
    if exp == 0:
        # subnormal number, leading zero
        frac = float(frac) / 0x800000
        return ((-1) ** sign) * math.ldexp(frac, -126)
    else:
        # normal number, leading one
        frac = float(frac + 0x8000000) / 0x1000000
        return ((-1) ** sign) * math.ldexp(frac, -127 + exp)


def int_from_float(val: float, nbits: int) -> int:
    # TODO: support real64, real128
    # method 1
    if nbits <= 32:
        return struct.unpack("I", struct.pack("f", val))[0]
    else:
        return struct.unpack("Q", struct.pack("d", val))[0]


def escape_filename(filename: str):
    trans = str.maketrans(":", "_")
    stem = Path(filename).stem.replace("*", "star")
    stem = stem.translate(trans)
    stem = re.sub(r"<.+>", "", stem)
    return Path(filename).with_stem(stem)
