# network/message.py
from enum import Enum

class MessageType(Enum):
    """
    BitTorrent protocol message types.
    """
    HANDSHAKE = 0
    BITFIELD = 1
    INTERESTED = 2
    NOT_INTERESTED = 3
    CHOKE = 4
    UNCHOKE = 5
    REQUEST = 6
    PIECE = 7
    HAVE = 8
    CANCEL = 9  # Additional message type (optional in implementation)

class Message:
    """
    Base message class for all BitTorrent protocol messages.
    """
    def __init__(self, msg_type, payload=None):
        self.msg_type = msg_type
        self.payload = payload if payload else {}
    
    def __str__(self):
        return f"{self.msg_type.name} Message: {self.payload}"

class HandshakeMessage(Message):
    """
    Handshake message sent when peers initially connect.
    Format: <header><peer_id>
    """
    def __init__(self, header, peer_id):
        super().__init__(
            MessageType.HANDSHAKE, 
            {'header': header, 'peer_id': peer_id}
        )
    
    def __str__(self):
        return f"HANDSHAKE: header={self.payload['header']}, peer_id={self.payload['peer_id']}"

class BitfieldMessage(Message):
    """
    Bitfield message indicating which pieces a peer has.
    """
    def __init__(self, pieces):
        super().__init__(
            MessageType.BITFIELD,
            {'pieces': pieces}
        )
    
    def __str__(self):
        return f"BITFIELD: {len(self.payload['pieces'])} pieces"

class InterestedMessage(Message):
    """
    Message indicating that a peer is interested in pieces from another peer.
    """
    def __init__(self):
        super().__init__(MessageType.INTERESTED)
    
    def __str__(self):
        return "INTERESTED"

class NotInterestedMessage(Message):
    """
    Message indicating that a peer is not interested in pieces from another peer.
    """
    def __init__(self):
        super().__init__(MessageType.NOT_INTERESTED)
    
    def __str__(self):
        return "NOT_INTERESTED"

class ChokeMessage(Message):
    """
    Message indicating that a peer is choking another peer.
    """
    def __init__(self):
        super().__init__(MessageType.CHOKE)
    
    def __str__(self):
        return "CHOKE"

class UnchokeMessage(Message):
    """
    Message indicating that a peer is unchoking another peer.
    """
    def __init__(self):
        super().__init__(MessageType.UNCHOKE)
    
    def __str__(self):
        return "UNCHOKE"

class RequestMessage(Message):
    """
    Message requesting a specific piece from another peer.
    """
    def __init__(self, piece_index):
        super().__init__(
            MessageType.REQUEST,
            {'piece_index': piece_index}
        )
    
    def __str__(self):
        return f"REQUEST: piece_index={self.payload['piece_index']}"

class PieceMessage(Message):
    """
    Message containing a piece of the file.
    """
    def __init__(self, piece_index, data):
        super().__init__(
            MessageType.PIECE,
            {'piece_index': piece_index, 'data': data}
        )
    
    def __str__(self):
        return f"PIECE: piece_index={self.payload['piece_index']}, data_length={len(str(self.payload['data']))}"

class HaveMessage(Message):
    """
    Message indicating that a peer has obtained a complete piece.
    """
    def __init__(self, piece_index):
        super().__init__(
            MessageType.HAVE,
            {'piece_index': piece_index}
        )
    
    def __str__(self):
        return f"HAVE: piece_index={self.payload['piece_index']}"

class CancelMessage(Message):
    """
    Message canceling a previous request for a piece.
    """
    def __init__(self, piece_index):
        super().__init__(
            MessageType.CANCEL,
            {'piece_index': piece_index}
        )
    
    def __str__(self):
        return f"CANCEL: piece_index={self.payload['piece_index']}"

# Message parsing utility functions
def parse_message(message_data):
    """
    Parse raw message data into appropriate message objects.
    In a real implementation, this would handle binary data.
    For the simulation, we'll assume messages are already in a structured format.
    """
    # This is a simplified implementation for the simulation
    if isinstance(message_data, dict):
        if 'message_type' in message_data:
            msg_type = message_data['message_type']
            
            if msg_type == "HANDSHAKE":
                return HandshakeMessage(
                    message_data.get('header', ''),
                    message_data.get('peer_id', '')
                )
            elif msg_type == "BITFIELD":
                return BitfieldMessage(message_data.get('pieces', []))
            elif msg_type == "INTERESTED":
                return InterestedMessage()
            elif msg_type == "NOT_INTERESTED":
                return NotInterestedMessage()
            elif msg_type == "CHOKE":
                return ChokeMessage()
            elif msg_type == "UNCHOKE":
                return UnchokeMessage()
            elif msg_type == "REQUEST":
                return RequestMessage(message_data.get('piece_index', 0))
            elif msg_type == "PIECE":
                return PieceMessage(
                    message_data.get('piece_index', 0),
                    message_data.get('data', None)
                )
            elif msg_type == "HAVE":
                return HaveMessage(message_data.get('piece_index', 0))
            elif msg_type == "CANCEL":
                return CancelMessage(message_data.get('piece_index', 0))
    
    return None