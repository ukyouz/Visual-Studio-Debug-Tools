import math
import struct
from functools import cache


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
def float_from_int(val: int) -> float:
    # method 1
    return struct.unpack('f', struct.pack('I', val))[0]

    # method 2
    sign = val >> 31
    exp = (val & 0x7F800000) >> 23
    frac = float((val & 0x007FFFFF) + 0x8000000) / 0x1000000
    return math.ldexp(frac, -126 + exp)


def int_from_float(val: float) -> int:
    m, e = math.frexp(val)
    return int((2 * m + (e + 125)) * 0x800000)
