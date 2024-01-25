from collections import deque


class DequeList(deque):

    def pop(self, n=None):
        if n is not None:
            self.rotate(-n)
            item = self.popleft()
            self.rotate(n)
            return item
        else:
            return super().pop()
