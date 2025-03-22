import os

class Configs:
    """
    Parses configuration files, stores and provides access
    to common simulator parameters and peer information.
    """
    def __init__(self, common_cfg_path, peer_info_path):
        self.common_cfg_path = common_cfg_path
        self.peer_info_path = peer_info_path
        
        # Example of storing parsed configurations
        self.piece_size = None
        self.file_name = None
        self.max_connections = None
        self.handshake_header = None
        
        self.peer_info = []  # Will store tuples/lists of (peer_id, hostname, port)
        
        self._parse_common_cfg()
        self._parse_peer_info()

    def _parse_common_cfg(self):
        with open(self.common_cfg_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=')
                    if key == 'PieceSize':
                        self.piece_size = int(value)
                    elif key == 'FileName':
                        self.file_name = value
                    elif key == 'MaxConnections':
                        self.max_connections = int(value)
                    elif key == 'HandshakeHeader':
                        self.handshake_header = value

    def _parse_peer_info(self):
        with open(self.peer_info_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    parts = line.strip().split()
                    peer_id = parts[0]
                    host = parts[1]
                    port = int(parts[2])
                    self.peer_info.append((peer_id, host, port))

    def __str__(self):
        return (
            f"Configs(\n"
            f"  piece_size={self.piece_size},\n"
            f"  file_name={self.file_name},\n"
            f"  max_connections={self.max_connections},\n"
            f"  handshake_header={self.handshake_header},\n"
            f"  peer_info={self.peer_info}\n"
            f")"
        )
