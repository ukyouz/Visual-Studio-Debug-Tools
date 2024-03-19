import math
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
