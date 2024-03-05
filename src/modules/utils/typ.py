import os
from collections import deque
from typing import Protocol


class DequeList(deque):

    def pop(self, n=None):
        if n is not None:
            self.rotate(-n)
            item = self.popleft()
            self.rotate(n)
            return item
        else:
            return super().pop()


class Stream(Protocol):
    def seek(self, offset: int, pos: int=os.SEEK_SET, /) -> int:
        ...

    def read(self, size: int) -> bytes:
        ...

    def write(self, buf: bytes, /) -> int:
        ...

    def tell(self) -> int:
        ...


