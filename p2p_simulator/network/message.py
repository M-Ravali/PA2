from enum import Enum

class MessageType(Enum):
    HANDSHAKE = 1
    BITFIELD = 2
    REQUEST = 3
    PIECE = 4
    CHOKE = 5
    UNCHOKE = 6
    INTERESTED = 7
    NOT_INTERESTED = 8

class Message:
    """
    Base message class. All specific message types
    (Handshake, Request, Piece, etc.) can extend this.
    """
    def __init__(self, msg_type, payload=None):
        self.msg_type = msg_type
        self.payload = payload

class HandshakeMessage(Message):
    def __init__(self, header, peer_id):
        super().__init__(MessageType.HANDSHAKE, payload={'header': header, 'peer_id': peer_id})

    def __str__(self):
        return f"HandshakeMessage(header={self.payload['header']}, peer_id={self.payload['peer_id']})"
