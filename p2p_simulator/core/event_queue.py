import heapq

class EventQueue:
    """
    Priority queue that stores events in chronological order.
    """
    def __init__(self):
        self._queue = []

    def push(self, event):
        heapq.heappush(self._queue, event)

    def pop(self):
        if self._queue:
            return heapq.heappop(self._queue)
        return None

    def is_empty(self):
        return len(self._queue) == 0
