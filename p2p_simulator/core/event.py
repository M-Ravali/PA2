class Event:
    """
    Represents a scheduled event in the simulator’s timeline.
    """
    def __init__(self, time, event_type, data=None):
        self.time = time
        self.event_type = event_type
        self.data = data

    def __lt__(self, other):
        """
        Allows sorting events by time in a priority queue.
        """
        return self.time < other.time

    def __repr__(self):
        return f"Event(time={self.time}, type={self.event_type}, data={self.data})"
