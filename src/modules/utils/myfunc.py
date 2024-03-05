from functools import lru_cache


@lru_cache
def BITMASK(bitcnt):
    return (1 << bitcnt) - 1

