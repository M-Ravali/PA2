# network/peer.py
import random
from enum import Enum
from collections import defaultdict
from .message import MessageType, Message, HandshakeMessage, BitfieldMessage, RequestMessage, PieceMessage, HaveMessage, InterestedMessage, NotInterestedMessage, ChokeMessage, UnchokeMessage

class PeerState(Enum):
    CHOKED = 0
    UNCHOKED = 1

class Peer:
    """
    Represents a P2P Peer that can be either a seeder or leecher.
    """
    def __init__(self, peer_id, host, port, config, is_seeder=False):
        self.peer_id = peer_id
        self.host = host
        self.port = port
        self.config = config
        
        # For tracking pieces
        self.total_pieces = config.total_pieces
        self.pieces = set()  # Pieces this peer has
        self.piece_requests = {}  # piece_index -> requesting_peer_id
        
        # For connections
        self.connected_peers = {}  # peer_id -> connection_state
        self.interested_peers = set()  # Peers interested in our pieces
        self.interested_in_peers = set()  # Peers we're interested in
        
        # For choke/unchoke mechanism
        self.unchoked_peers = set()  # Peers we've unchoked
        self.choked_by_peers = set()  # Peers that have choked us
        self.download_rates = defaultdict(float)  # peer_id -> rate
        
        # For performance tracking
        self.total_downloaded = 0
        self.download_start_time = None
        self.download_complete_time = None
        
        # For simulation metrics
        self.piece_arrival_times = {}  # piece_index -> arrival_time
        
        # If this is a seeder, it starts with all pieces
        if is_seeder:
            for i in range(self.total_pieces):
                self.pieces.add(i)
    
    def handle_event(self, event, simulator):
        """
        Process an event directed at this peer.
        """
        event_type = event.event_type
        data = event.data
        current_time = event.time
        
        if event_type == "PEER_CONNECTION":
            # A peer has requested connection, send handshake
            other_peer_id = data['from_peer_id']
            self.connected_peers[other_peer_id] = PeerState.CHOKED
            
            # Schedule handshake response
            simulator.schedule_event(
                current_time + 0.1,
                "HANDSHAKE",
                {
                    'from_peer_id': self.peer_id,
                    'to_peer_id': other_peer_id
                }
            )
            
        elif event_type == "HANDSHAKE":
            # Received handshake, send bitfield
            other_peer_id = data['from_peer_id']
            
            # Schedule bitfield message
            simulator.schedule_event(
                current_time + 0.1,
                "BITFIELD",
                {
                    'from_peer_id': self.peer_id,
                    'to_peer_id': other_peer_id,
                    'pieces': list(self.pieces)
                }
            )
            
        elif event_type == "BITFIELD":
            # Received bitfield, determine interest
            other_peer_id = data['from_peer_id']
            pieces = set(data['pieces'])
            
            # Determine if we're interested
            missing_pieces = pieces - self.pieces
            if missing_pieces:
                self.interested_in_peers.add(other_peer_id)
                
                # Schedule interested message
                simulator.schedule_event(
                    current_time + 0.1,
                    "INTERESTED",
                    {
                        'from_peer_id': self.peer_id,
                        'to_peer_id': other_peer_id
                    }
                )
            else:
                # Schedule not interested message
                simulator.schedule_event(
                    current_time + 0.1,
                    "NOT_INTERESTED",
                    {
                        'from_peer_id': self.peer_id,
                        'to_peer_id': other_peer_id
                    }
                )
                
        elif event_type == "INTERESTED":
            # A peer is interested in our pieces
            other_peer_id = data['from_peer_id']
            self.interested_peers.add(other_peer_id)
            
            # Decide whether to unchoke based on tit-for-tat
            # For simulation, unchoke with probability based on download rate
            if (other_peer_id in self.download_rates and 
                self.download_rates[other_peer_id] > 0) or random.random() < 0.3:
                self.unchoked_peers.add(other_peer_id)
                
                # Schedule unchoke message
                simulator.schedule_event(
                    current_time + 0.1,
                    "UNCHOKE",
                    {
                        'from_peer_id': self.peer_id,
                        'to_peer_id': other_peer_id
                    }
                )
            
        elif event_type == "NOT_INTERESTED":
            # A peer is not interested in our pieces
            other_peer_id = data['from_peer_id']
            if other_peer_id in self.interested_peers:
                self.interested_peers.remove(other_peer_id)
            
        elif event_type == "UNCHOKE":
            # We've been unchoked, can request pieces
            other_peer_id = data['from_peer_id']
            if other_peer_id in self.choked_by_peers:
                self.choked_by_peers.remove(other_peer_id)
            
            # If we're interested, schedule a piece request
            if other_peer_id in self.interested_in_peers:
                # Find a piece to request
                requested_piece = self._select_piece_to_request(other_peer_id)
                if requested_piece is not None:
                    # Schedule request
                    simulator.schedule_event(
                        current_time + 0.1,
                        "REQUEST",
                        {
                            'from_peer_id': self.peer_id,
                            'to_peer_id': other_peer_id,
                            'piece_index': requested_piece
                        }
                    )
        
        elif event_type == "CHOKE":
            # We've been choked
            other_peer_id = data['from_peer_id']
            self.choked_by_peers.add(other_peer_id)
            
        elif event_type == "REQUEST":
            # A peer requests a piece
            other_peer_id = data['from_peer_id']
            piece_index = data['piece_index']
            
            # If we have the piece and peer is unchoked, send it
            if piece_index in self.pieces and other_peer_id in self.unchoked_peers:
                # Schedule piece message
                simulator.schedule_event(
                    current_time + random.uniform(0.2, 0.5),  # Random delay for network simulation
                    "PIECE",
                    {
                        'from_peer_id': self.peer_id,
                        'to_peer_id': other_peer_id,
                        'piece_index': piece_index,
                        'data': f"PIECE_DATA_{piece_index}"  # Simulated piece data
                    }
                )
        
        elif event_type == "PIECE":
            # Received a piece
            other_peer_id = data['from_peer_id']
            piece_index = data['piece_index']
            piece_data = data['data']
            
            # Add to our pieces
            self.pieces.add(piece_index)
            self.total_downloaded += 1
            self.piece_arrival_times[piece_index] = current_time
            
            # Update download rate
            if other_peer_id in self.download_rates:
                self.download_rates[other_peer_id] += 1
            else:
                self.download_rates[other_peer_id] = 1
            
            # Schedule have message to all connected peers
            for peer_id in self.connected_peers:
                simulator.schedule_event(
                    current_time + 0.1,
                    "HAVE",
                    {
                        'from_peer_id': self.peer_id,
                        'to_peer_id': peer_id,
                        'piece_index': piece_index
                    }
                )
            
            # Check if download is complete
            if len(self.pieces) == self.total_pieces:
                self.download_complete_time = current_time
                # Could schedule additional events for download completion
            else:
                # Request more pieces from unchoked peers
                for peer_id in self.interested_in_peers:
                    if peer_id not in self.choked_by_peers:
                        requested_piece = self._select_piece_to_request(peer_id)
                        if requested_piece is not None:
                            simulator.schedule_event(
                                current_time + 0.2,
                                "REQUEST",
                                {
                                    'from_peer_id': self.peer_id,
                                    'to_peer_id': peer_id,
                                    'piece_index': requested_piece
                                }
                            )
        
        elif event_type == "HAVE":
            # A peer has a new piece
            other_peer_id = data['from_peer_id']
            piece_index = data['piece_index']
            
            # If we don't have this piece, express interest
            if piece_index not in self.pieces and other_peer_id not in self.interested_in_peers:
                self.interested_in_peers.add(other_peer_id)
                
                # Schedule interested message
                simulator.schedule_event(
                    current_time + 0.1,
                    "INTERESTED",
                    {
                        'from_peer_id': self.peer_id,
                        'to_peer_id': other_peer_id
                    }
                )
        
        elif event_type == "OPTIMISTIC_UNCHOKE":
            # Perform optimistic unchoke
            if self.interested_peers:
                # Choose a random peer to unchoke
                candidate_peers = list(self.interested_peers - self.unchoked_peers)
                if candidate_peers:
                    lucky_peer = random.choice(candidate_peers)
                    self.unchoked_peers.add(lucky_peer)
                    
                    # Schedule unchoke message
                    simulator.schedule_event(
                        current_time + 0.1,
                        "UNCHOKE",
                        {
                            'from_peer_id': self.peer_id,
                            'to_peer_id': lucky_peer
                        }
                    )
    
    def _select_piece_to_request(self, peer_id):
        """
        Implement the piece selection algorithm (Local Rarest First)
        """
        # In a real implementation, we would track piece frequencies across peers
        # For simplicity, choose a random piece we don't have but the peer has
        # This would be replaced with actual rarest-first logic
        
        # This is a placeholder for now
        available_pieces = set()
        for i in range(self.total_pieces):
            if i not in self.pieces:
                available_pieces.add(i)
        
        if available_pieces:
            return random.choice(list(available_pieces))
        return None
    
    def connect_to_peer(self, peer_id, simulator, current_time):
        """
        Initiate connection to another peer
        """
        if peer_id not in self.connected_peers:
            self.connected_peers[peer_id] = PeerState.CHOKED
            
            # Schedule connection event
            simulator.schedule_event(
                current_time + 0.1,
                "PEER_CONNECTION",
                {
                    'from_peer_id': self.peer_id,
                    'to_peer_id': peer_id
                }
            )
            return True
        return False

# core/simulator.py
class Simulator:
    """
    Main event-driven simulator for BitTorrent.
    """
    def __init__(self, event_queue, peers, tracker=None):
        self.event_queue = event_queue
        self.peers = peers  # Dict of peer_id -> Peer
        self.tracker = tracker
        self.current_time = 0
        self.stats = {
            'total_events_processed': 0,
            'piece_transfers': 0,
            'peer_connections': 0,
            'download_completions': 0
        }
    
    def run(self, end_time=1000):
        """
        Run the simulation until the specified end time or until no more events.
        """
        while not self.event_queue.is_empty():
            event = self.event_queue.pop()
            
            if event.time > end_time:
                break
            
            self.current_time = event.time
            self.dispatch_event(event)
            self.stats['total_events_processed'] += 1
            
            # Periodically perform optimistic unchoke
            if int(self.current_time) % 30 == 0:
                for peer_id, peer in self.peers.items():
                    self.schedule_event(
                        self.current_time,
                        "OPTIMISTIC_UNCHOKE",
                        {'peer_id': peer_id}
                    )
    
    def dispatch_event(self, event):
        """
        Dispatch an event to the appropriate peer or handle it globally.
        """
        event_type = event.event_type
        data = event.data
        
        if event_type == "TRACKER_ANNOUNCE":
            # Handle tracker announcements
            if self.tracker:
                self.tracker.handle_announce(data['peer_id'], self)
        
        elif 'to_peer_id' in data:
            # Peer-to-peer message
            to_peer_id = data['to_peer_id']
            if to_peer_id in self.peers:
                self.peers[to_peer_id].handle_event(event, self)
                
                # Track statistics
                if event_type == "PIECE":
                    self.stats['piece_transfers'] += 1
                elif event_type == "PEER_CONNECTION":
                    self.stats['peer_connections'] += 1
        
        elif 'peer_id' in data:
            # Direct peer event
            peer_id = data['peer_id']
            if peer_id in self.peers:
                self.peers[peer_id].handle_event(event, self)
    
    def schedule_event(self, time, event_type, data=None):
        """
        Schedule a new event.
        """
        from core.event import Event
        ev = Event(time, event_type, data)
        self.event_queue.push(ev)
    
    def initialize_connections(self):
        """
        Initialize peer connections based on tracker information.
        """
        if self.tracker:
            for peer_id, peer in self.peers.items():
                # Simulate peer discovering others through tracker
                peer_list = self.tracker.get_peers(peer_id)
                
                # Establish connections (each peer connects to a subset)
                for other_id in peer_list[:min(5, len(peer_list))]:
                    peer.connect_to_peer(other_id, self, self.current_time)
    
    def get_statistics(self):
        """
        Collect and return statistics about the simulation.
        """
        stats = self.stats.copy()
        
        # Add peer statistics
        peer_stats = {}
        for peer_id, peer in self.peers.items():
            if peer.download_complete_time:
                completion_time = peer.download_complete_time
                if peer.download_start_time:
                    download_duration = completion_time - peer.download_start_time
                else:
                    download_duration = completion_time
                
                peer_stats[peer_id] = {
                    'completion_time': completion_time,
                    'download_duration': download_duration,
                    'pieces_count': len(peer.pieces),
                    'piece_arrival_times': peer.piece_arrival_times
                }
        
        stats['peer_stats'] = peer_stats
        stats['active_peers_over_time'] = self._calculate_active_peers_over_time()
        
        return stats
    
    def _calculate_active_peers_over_time(self):
        """
        Calculate the number of active peers over time.
        """
        # This would track peers that are still downloading
        # For a real implementation, we'd need to track join/leave events
        active_peers = {}
        time_points = sorted(set([0] + [
            peer.download_complete_time for peer in self.peers.values() 
            if peer.download_complete_time is not None
        ]))
        
        for t in time_points:
            count = sum(
                1 for peer in self.peers.values() 
                if peer.download_complete_time is None or peer.download_complete_time > t
            )
            active_peers[t] = count
        
        return active_peers