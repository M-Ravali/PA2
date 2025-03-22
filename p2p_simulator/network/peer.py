import socket
import threading
import queue

from .message import MessageType, HandshakeMessage
from ..utils.logger import P2PLog

class Peer:
    """
    Represents a P2P Peer with an ID, ability to connect
    to other peers, send/receive messages, and handle events.
    """
    def __init__(self, peer_id, host, port, config):
        self.peer_id = peer_id
        self.host = host
        self.port = port
        self.config = config
        
        self.log = P2PLog(peer_id)
        self.connected_peers = {}  # peer_id -> socket
        
        # For demonstration, store events in a thread-safe queue
        self.event_queue = queue.Queue()

        # Example: Track which pieces we have
        self.pieces = set()
        
        # Start listening server in a separate thread
        self._server_thread = threading.Thread(target=self.listen_for_connections)
        self._server_thread.start()

    def listen_for_connections(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(self.config.max_connections)
        self.log.info(f"Peer {self.peer_id} listening on {self.host}:{self.port}")
        
        while True:
            conn, addr = server_socket.accept()
            # For simplicity, handle each connection in a new thread
            threading.Thread(target=self.handle_connection, args=(conn, addr)).start()

    def handle_connection(self, conn, addr):
        # On receiving a connection, parse a handshake message
        data = conn.recv(1024)
        if data:
            # Assume the data is a handshake for demonstration
            self.log.info(f"Received handshake from {addr}")
            # You would parse the handshake properly here
            # Then possibly push an event
            self.event_queue.put(("HANDSHAKE_RECEIVED", addr))

        # Keep listening for subsequent messages
        while True:
            data = conn.recv(4096)
            if not data:
                break
            # Handle the data (parse message, etc.)
            # Potentially trigger event(s)
            self.event_queue.put(("MESSAGE_RECEIVED", data))

    def connect_to_peer(self, other_peer_id, host, port):
        if other_peer_id in self.connected_peers:
            return
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        self.connected_peers[other_peer_id] = s
        
        # Send handshake
        handshake = HandshakeMessage(self.config.handshake_header, self.peer_id)
        s.sendall(str(handshake).encode('utf-8'))
        self.log.info(f"Sent handshake to peer {other_peer_id}")

    def send_message(self, peer_id, message):
        if peer_id in self.connected_peers:
            s = self.connected_peers[peer_id]
            s.sendall(str(message).encode('utf-8'))
            self.log.debug(f"Sent message to {peer_id}: {message}")
        else:
            self.log.error(f"Cannot send message to {peer_id}. Not connected.")

    def process_event(self, event):
        """
        Handle events popped off the event queue. This method
        could be invoked by the simulator or a loop in the peer.
        """
        event_type, event_data = event
        if event_type == "HANDSHAKE_RECEIVED":
            self.log.info(f"Processing handshake event from {event_data}.")
        elif event_type == "MESSAGE_RECEIVED":
            # Parse the message, etc.
            self.log.info("Processing message event.")
        else:
            self.log.error(f"Unknown event type: {event_type}")
