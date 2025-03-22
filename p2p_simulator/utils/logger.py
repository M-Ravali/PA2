import logging
import os

class P2PLog:
    def __init__(self, peer_id):
        self.logger = logging.getLogger(f"Peer-{peer_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # Create file handler
        log_filename = f"peer_{peer_id}.log"
        fh = logging.FileHandler(log_filename)
        fh.setLevel(logging.DEBUG)
        
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def info(self, msg):
        self.logger.info(msg)

    def debug(self, msg):
        self.logger.debug(msg)

    def error(self, msg):
        self.logger.error(msg)
