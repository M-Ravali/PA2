# utils/configs.py
import os

class Configs:
    """
    Parses configuration files and provides access to BitTorrent simulation parameters.
    """
    def __init__(self, common_cfg_path=None, peer_info_path=None):
        # Default values
        self.piece_size = 1024
        self.file_name = "sample_file.dat"
        self.max_connections = 5
        self.handshake_header = "P2PFILESHARINGPROJ"
        self.total_pieces = 100
        self.total_peers = 20
        self.total_seeders = 1
        self.simulation_end_time = 1000
        self.speed_factor = 1.0  # Default speed factor
        
        self.peer_info = []  # Will store tuples of (peer_id, hostname, port)
        
        # Parse configuration files if provided
        if common_cfg_path and os.path.exists(common_cfg_path):
            self._parse_common_cfg(common_cfg_path)
            
        if peer_info_path and os.path.exists(peer_info_path):
            self._parse_peer_info(peer_info_path)

    def _parse_common_cfg(self, path):
        """
        Parse the common configuration file.
        """
        with open(path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    try:
                        key, value = line.strip().split('=')
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'PieceSize':
                            self.piece_size = int(value)
                        elif key == 'FileName':
                            self.file_name = value
                        elif key == 'MaxConnections':
                            self.max_connections = int(value)
                        elif key == 'HandshakeHeader':
                            self.handshake_header = value.strip('"')
                        elif key == 'TotalPieces':
                            self.total_pieces = int(value)
                        elif key == 'TotalPeers':
                            self.total_peers = int(value)
                        elif key == 'TotalSeeders':
                            self.total_seeders = int(value)
                        elif key == 'SimulationEndTime':
                            self.simulation_end_time = int(value)
                        elif key == 'SpeedFactor':
                            self.speed_factor = float(value)
                    except ValueError:
                        print(f"Warning: Malformed line in config: {line}")

    def _parse_peer_info(self, path):
        """
        Parse the peer information file.
        """
        with open(path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    try:
                        parts = line.strip().split()
                        peer_id = parts[0]
                        host = parts[1]
                        port = int(parts[2])
                        self.peer_info.append((peer_id, host, port))
                    except (ValueError, IndexError):
                        print(f"Warning: Malformed line in peer info: {line}")

    def __str__(self):
        """
        String representation of the configuration.
        """
        return (
            f"Configs(\n"
            f"  piece_size={self.piece_size},\n"
            f"  file_name={self.file_name},\n"
            f"  max_connections={self.max_connections},\n"
            f"  handshake_header={self.handshake_header},\n"
            f"  total_pieces={self.total_pieces},\n"
            f"  total_peers={self.total_peers},\n"
            f"  total_seeders={self.total_seeders},\n"
            f"  simulation_end_time={self.simulation_end_time},\n"
            f"  speed_factor={self.speed_factor},\n"
            f"  peer_info={self.peer_info}\n"
            f")"
        )