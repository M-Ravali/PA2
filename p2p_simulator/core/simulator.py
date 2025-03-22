import time

class Simulator:
    """
    Main event-driven simulator. Manages the global timeline,
    event queue, and can coordinate the behavior of multiple peers.
    """
    def __init__(self, event_queue, peers):
        self.event_queue = event_queue
        self.peers = peers
        self.current_time = 0
    
    def run(self, end_time=1000):
        """
        Run the simulation until the specified end time or 
        until there are no more events.
        """
        while not self.event_queue.is_empty():
            event = self.event_queue.pop()
            if event.time > end_time:
                break
            
            self.current_time = event.time
            self.dispatch_event(event)
            
            # In a real simulator, you might do time.sleep() or 
            # process multiple events that occur at the same time.
    
    def dispatch_event(self, event):
        event_type = event.event_type
        data = event.data
        
        # Example: Identify which Peer to deliver the event to
        if 'peer_id' in data:
            peer_id = data['peer_id']
            if peer_id in self.peers:
                self.peers[peer_id].process_event((event_type, data))
        else:
            # Or handle globally
            pass

    def schedule_event(self, time, event_type, data=None):
        from .event import Event
        ev = Event(time, event_type, data)
        self.event_queue.push(ev)
