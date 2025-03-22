# core/event.py
class Event:
    """
    Represents a scheduled event in the BitTorrent simulator.
    Events are ordered by time in the priority queue.
    """
    def __init__(self, time, event_type, data=None):
        """
        Initialize a new Event.
        
        Args:
            time (float): The time at which this event occurs.
            event_type (str): The type of event (e.g., "HANDSHAKE", "REQUEST", etc.).
            data (dict, optional): Additional data needed for this event. Defaults to None.
        """
        self.time = time
        self.event_type = event_type
        self.data = data if data is not None else {}

    def __lt__(self, other):
        """
        Compare events based on their scheduled time.
        This allows the priority queue to order events chronologically.
        
        Args:
            other (Event): Another event to compare with.
            
        Returns:
            bool: True if this event should occur before the other event.
        """
        if not isinstance(other, Event):
            return NotImplemented
        return self.time < other.time
    
    def __eq__(self, other):
        """
        Check if two events are equal.
        
        Args:
            other (Event): Another event to compare with.
            
        Returns:
            bool: True if the events have the same time, type, and data.
        """
        if not isinstance(other, Event):
            return NotImplemented
        return (self.time == other.time and 
                self.event_type == other.event_type and 
                self.data == other.data)
    
    def __repr__(self):
        """
        Return a string representation of the event.
        
        Returns:
            str: A string describing the event.
        """
        return f"Event(time={self.time:.2f}, type={self.event_type}, data={self.data})"