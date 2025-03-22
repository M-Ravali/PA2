import os

class FileHandler:
    """
    Handles reading/writing pieces of a file.
    """
    def __init__(self, file_name, piece_size):
        self.file_name = file_name
        self.piece_size = piece_size
        self.file_size = os.path.getsize(file_name) if os.path.exists(file_name) else 0
    
    def read_piece(self, piece_index):
        """
        Reads a piece of size `piece_size` from `file_name`.
        """
        with open(self.file_name, 'rb') as f:
            f.seek(piece_index * self.piece_size)
            return f.read(self.piece_size)

    def write_piece(self, piece_index, data):
        """
        Writes a piece of data (<= piece_size) to `file_name`.
        """
        with open(self.file_name, 'r+b') as f:
            f.seek(piece_index * self.piece_size)
            f.write(data)
