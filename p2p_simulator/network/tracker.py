# network/tracker.py
import random

class Tracker:
    """
    Represents the BitTorrent tracker that helps peers find each other.
    """
    def __init__(self, config):
        self.config = config
        self.registered_peers = {}  # peer_id -> (host, port, pieces)
        self.peer_stats = {}  # peer_id -> stats
    
    def register_peer(self, peer_id, host, port, pieces):
        """
        Register a peer with the tracker.
        """
        self.registered_peers[peer_id] = (host, port, pieces)
        self.peer_stats[peer_id] = {
            'announced': 0,
            'bytes_downloaded': 0,
            'pieces': len(pieces)
        }
    
    def update_peer(self, peer_id, pieces):
        """
        Update the peer's information.
        """
        if peer_id in self.registered_peers:
            host, port, _ = self.registered_peers[peer_id]
            self.registered_peers[peer_id] = (host, port, pieces)
            self.peer_stats[peer_id]['pieces'] = len(pieces)
            self.peer_stats[peer_id]['announced'] += 1
    
    def handle_announce(self, peer_id, simulator):
        """
        Handle an announce from a peer, sending back peer list.
        """
        if peer_id not in self.registered_peers:
            return
        
        # Update stats
        self.peer_stats[peer_id]['announced'] += 1
        
        # Schedule events for the peer to connect to others
        current_time = simulator.current_time
        peer_list = self.get_peers(peer_id)
        
        # Schedule the next announce
        simulator.schedule_event(
            current_time + random.uniform(30, 60),  # Announce interval
            "TRACKER_ANNOUNCE",
            {'peer_id': peer_id}
        )
    
    def get_peers(self, requesting_peer_id):
        """
        Return a list of peer_ids that the requesting peer can connect to.
        """
        # Return all peers except the requesting one
        return [pid for pid in self.registered_peers.keys() 
                if pid != requesting_peer_id]
    
    def get_peer_info(self, peer_id):
        """
        Get detailed info about a specific peer.
        """
        if peer_id in self.registered_peers:
            host, port, pieces = self.registered_peers[peer_id]
            return {
                'host': host,
                'port': port,
                'pieces_count': len(pieces),
                'stats': self.peer_stats.get(peer_id, {})
            }
        return None