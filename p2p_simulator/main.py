# graph_main.py
"""
BitTorrent simulator with file-only matplotlib backend to generate graphs
without needing Tcl/Tk or interactive display.
"""

import random
import time
import os
import sys
import json
from datetime import datetime

# First, set matplotlib backend to Agg (non-interactive, file-only)
import matplotlib
matplotlib.use('Agg')  # This MUST come before importing pyplot
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Define simplified versions of our classes
class Event:
    def __init__(self, time, event_type, data=None):
        self.time = time
        self.event_type = event_type
        self.data = data if data is not None else {}
        
    def __lt__(self, other):
        return self.time < other.time
        
    def __repr__(self):
        return f"Event(time={self.time:.2f}, type={self.event_type})"

class EventQueue:
    def __init__(self):
        self._queue = []
        
    def push(self, event):
        print(f"Adding event to queue: {event}")
        self._queue.append(event)
        self._queue.sort()  # Simple sort instead of heapq for debugging
        
    def pop(self):
        if not self._queue:
            return None
        return self._queue.pop(0)
        
    def is_empty(self):
        return len(self._queue) == 0
        
    def size(self):
        return len(self._queue)

class Peer:
    def __init__(self, peer_id, is_seeder=False, download_speed=1.0):
        self.peer_id = peer_id
        self.is_seeder = is_seeder
        self.download_speed = download_speed
        self.pieces = set()
        self.piece_arrival_times = {}  # piece_index -> arrival_time
        self.download_complete_time = None
        self.download_start_time = 0  # Assume starts at simulation time 0
        self.piece_count_over_time = [(0, 0)]  # (time, pieces) tuples
        
        if is_seeder:
            # Seeders start with all pieces
            for i in range(10):  # Simplified: just 10 pieces for debugging
                self.pieces.add(i)
                self.piece_arrival_times[i] = 0
            self.piece_count_over_time = [(0, 10)]
        
        self.connected_peers = []
        print(f"Created peer {peer_id} (Seeder: {is_seeder}, Speed: {download_speed})")
        
    def handle_event(self, event, simulator):
        print(f"Peer {self.peer_id} handling event: {event.event_type}")
        # Add simple event handling
        if event.event_type == "CONNECT":
            target_peer_id = event.data.get('target_peer_id')
            if target_peer_id and target_peer_id not in self.connected_peers:
                self.connected_peers.append(target_peer_id)
                print(f"Peer {self.peer_id} connected to {target_peer_id}")
                
                # Schedule handshake
                simulator.schedule_event(
                    simulator.current_time + 0.1,
                    "HANDSHAKE",
                    {
                        'from_peer_id': self.peer_id,
                        'to_peer_id': target_peer_id
                    }
                )
        
        elif event.event_type == "HANDSHAKE":
            from_peer_id = event.data.get('from_peer_id')
            print(f"Peer {self.peer_id} received handshake from {from_peer_id}")
            
            # Schedule bitfield
            simulator.schedule_event(
                simulator.current_time + 0.1,
                "BITFIELD",
                {
                    'from_peer_id': self.peer_id,
                    'to_peer_id': from_peer_id,
                    'pieces': list(self.pieces)
                }
            )
            
        elif event.event_type == "BITFIELD":
            from_peer_id = event.data.get('from_peer_id')
            pieces = event.data.get('pieces', [])
            print(f"Peer {self.peer_id} received bitfield from {from_peer_id} with {len(pieces)} pieces")
            
            # If we're missing pieces, express interest
            if not self.is_seeder:
                simulator.schedule_event(
                    simulator.current_time + 0.1,
                    "INTERESTED",
                    {
                        'from_peer_id': self.peer_id,
                        'to_peer_id': from_peer_id
                    }
                )
                
        elif event.event_type == "INTERESTED":
            from_peer_id = event.data.get('from_peer_id')
            print(f"Peer {self.peer_id} received interest from {from_peer_id}")
            
            # Unchoke the peer
            simulator.schedule_event(
                simulator.current_time + 0.1,
                "UNCHOKE",
                {
                    'from_peer_id': self.peer_id,
                    'to_peer_id': from_peer_id
                }
            )
            
        elif event.event_type == "UNCHOKE":
            from_peer_id = event.data.get('from_peer_id')
            print(f"Peer {self.peer_id} was unchoked by {from_peer_id}")
            
            # Request a piece if we're not a seeder
            if not self.is_seeder:
                # Find a piece we don't have
                missing_pieces = [i for i in range(10) if i not in self.pieces]
                if missing_pieces:
                    piece_to_request = random.choice(missing_pieces)
                    simulator.schedule_event(
                        simulator.current_time + 0.1,
                        "REQUEST",
                        {
                            'from_peer_id': self.peer_id,
                            'to_peer_id': from_peer_id,
                            'piece_index': piece_to_request
                        }
                    )
        
        elif event.event_type == "REQUEST":
            from_peer_id = event.data.get('from_peer_id')
            piece_index = event.data.get('piece_index')
            print(f"Peer {self.peer_id} received request for piece {piece_index} from {from_peer_id}")
            
            # Send the piece if we have it
            if piece_index in self.pieces:
                # Apply transfer speed of the receiving peer
                receiving_peer = simulator.peers.get(from_peer_id)
                if receiving_peer:
                    delay = 0.5 / receiving_peer.download_speed  # Base delay divided by speed factor
                else:
                    delay = 0.5  # Default delay
                
                simulator.schedule_event(
                    simulator.current_time + delay,
                    "PIECE",
                    {
                        'from_peer_id': self.peer_id,
                        'to_peer_id': from_peer_id,
                        'piece_index': piece_index,
                        'data': f"data_for_piece_{piece_index}"
                    }
                )
                
        elif event.event_type == "PIECE":
            from_peer_id = event.data.get('from_peer_id')
            piece_index = event.data.get('piece_index')
            print(f"Peer {self.peer_id} received piece {piece_index} from {from_peer_id}")
            
            # Add the piece to our collection
            self.pieces.add(piece_index)
            self.piece_arrival_times[piece_index] = simulator.current_time
            
            # Update piece count over time
            self.piece_count_over_time.append((simulator.current_time, len(self.pieces)))
            
            # Broadcast HAVE message
            for peer_id in self.connected_peers:
                simulator.schedule_event(
                    simulator.current_time + 0.1,
                    "HAVE",
                    {
                        'from_peer_id': self.peer_id,
                        'to_peer_id': peer_id,
                        'piece_index': piece_index
                    }
                )
                
            # Request another piece if we're not complete
            if len(self.pieces) < 10:  # Less than all pieces
                missing_pieces = [i for i in range(10) if i not in self.pieces]
                if missing_pieces:
                    piece_to_request = random.choice(missing_pieces)
                    simulator.schedule_event(
                        simulator.current_time + 0.1,
                        "REQUEST",
                        {
                            'from_peer_id': self.peer_id,
                            'to_peer_id': from_peer_id,
                            'piece_index': piece_to_request
                        }
                    )
            else:
                self.download_complete_time = simulator.current_time
                print(f"Peer {self.peer_id} has completed download at time {self.download_complete_time:.2f}!")
                
        elif event.event_type == "HAVE":
            from_peer_id = event.data.get('from_peer_id')
            piece_index = event.data.get('piece_index')
            print(f"Peer {self.peer_id} received HAVE message for piece {piece_index} from {from_peer_id}")

class Simulator:
    def __init__(self, event_queue, peers):
        self.event_queue = event_queue
        self.peers = peers
        self.current_time = 0
        self.stats = {
            'events_processed': 0,
            'piece_transfers': 0,
            'peer_stats': {},
            'active_peers_over_time': []  # Will store (time, count) tuples
        }
        
    def run(self, max_time=100, max_events=1000):
        """Run the simulation with additional safety limits."""
        events_processed = 0
        print(f"Starting simulation with {len(self.peers)} peers")
        print(f"Queue has {self.event_queue.size()} initial events")
        
        start_time = time.time()
        last_snapshot_time = 0
        
        while not self.event_queue.is_empty():
            if events_processed >= max_events:
                print(f"Reached maximum events limit ({max_events})")
                break
                
            if time.time() - start_time > 20:  # Safety timeout
                print("Simulation timeout reached!")
                break
                
            event = self.event_queue.pop()
            
            if event.time > max_time:
                print(f"Reached maximum simulation time ({max_time})")
                break
                
            print(f"\nProcessing event #{events_processed}: {event}")
            self.current_time = event.time
            self.dispatch_event(event)
            events_processed += 1
            self.stats['events_processed'] = events_processed
            
            # Periodically track active peers (once per simulation time unit)
            if int(self.current_time) > last_snapshot_time:
                active_count = sum(1 for p in self.peers.values() 
                                  if not p.is_seeder and 
                                  (p.download_complete_time is None or 
                                   p.download_complete_time > self.current_time))
                self.stats['active_peers_over_time'].append((self.current_time, active_count))
                last_snapshot_time = int(self.current_time)
            
            # Brief pause to make output readable
            time.sleep(0.01)
            
        print(f"\nSimulation finished after {events_processed} events")
        print(f"Final simulation time: {self.current_time:.2f}")
        
        # Collect peer stats
        for peer_id, peer in self.peers.items():
            piece_count_dataframe = pd.DataFrame(
                peer.piece_count_over_time, 
                columns=['time', 'pieces']
            )
            
            self.stats['peer_stats'][peer_id] = {
                'pieces': len(peer.pieces),
                'download_complete_time': peer.download_complete_time,
                'piece_arrival_times': peer.piece_arrival_times,
                'download_speed': peer.download_speed,
                'piece_count_over_time': piece_count_dataframe.to_dict(orient='records')
            }
        
        print(f"Stats: {self.stats['events_processed']} events processed, {self.stats['piece_transfers']} piece transfers")
        
        # Print peer stats
        print("\nPeer Stats:")
        for peer_id, peer in self.peers.items():
            status = "Complete" if len(peer.pieces) == 10 else "Incomplete"
            completion_time = peer.download_complete_time if peer.download_complete_time else "N/A"
            print(f"Peer {peer_id}: {len(peer.pieces)}/10 pieces ({status}), Completion time: {completion_time}")
            
        return self.stats
            
    def dispatch_event(self, event):
        """Dispatch event to appropriate peer."""
        try:
            if 'to_peer_id' in event.data:
                to_peer_id = event.data['to_peer_id']
                if to_peer_id in self.peers:
                    self.peers[to_peer_id].handle_event(event, self)
                else:
                    print(f"Warning: Event targeted at unknown peer {to_peer_id}")
            elif 'peer_id' in event.data:
                peer_id = event.data['peer_id']
                if peer_id in self.peers:
                    self.peers[peer_id].handle_event(event, self)
                else:
                    print(f"Warning: Event for unknown peer {peer_id}")
            else:
                print(f"Warning: Event has no target peer: {event}")
                
            # Track piece transfers
            if event.event_type == "PIECE":
                self.stats['piece_transfers'] += 1
        except Exception as e:
            print(f"Error dispatching event: {e}")
            
    def schedule_event(self, time, event_type, data=None):
        """Schedule a new event."""
        event = Event(time, event_type, data)
        self.event_queue.push(event)
        return event
        
def run_simulation_with_varying_peers(base_peers=5, max_peers=20, step=5):
    """Run multiple simulations with different numbers of peers."""
    results = []
    
    for num_peers in range(base_peers, max_peers + 1, step):
        print(f"\n=== Running simulation with {num_peers} peers ===\n")
        
        # Create event queue
        event_queue = EventQueue()
        
        # Create peers (1 seeder, rest leechers)
        peers = {}
        peers['peer1'] = Peer('peer1', is_seeder=True)
        
        for i in range(2, num_peers + 1):
            peer_id = f'peer{i}'
            peers[peer_id] = Peer(peer_id, is_seeder=False)
        
        # Create simulator
        simulator = Simulator(event_queue, peers)
        
        # Schedule initial connection events
        # Connect all leechers to the seeder
        for i in range(2, num_peers + 1):
            peer_id = f'peer{i}'
            simulator.schedule_event(
                0.1 * (i - 1),  # Stagger connections
                "CONNECT",
                {
                    'peer_id': peer_id,
                    'target_peer_id': 'peer1'
                }
            )
        
        # Also connect some peers to each other (partial mesh)
        for i in range(2, num_peers + 1, 2):
            if i + 1 <= num_peers:
                peer_id = f'peer{i}'
                target_id = f'peer{i+1}'
                simulator.schedule_event(
                    5.0 + 0.1 * (i - 1),  # Connect after initial downloads start
                    "CONNECT",
                    {
                        'peer_id': peer_id,
                        'target_peer_id': target_id
                    }
                )
        
        # Run simulation
        stats = simulator.run(max_time=100, max_events=1000)
        
        # Calculate average completion time
        completion_times = []
        for peer_id, peer_stat in stats['peer_stats'].items():
            if not peer_id == 'peer1' and peer_stat['download_complete_time'] is not None:
                completion_times.append(peer_stat['download_complete_time'])
        
        avg_completion = sum(completion_times) / len(completion_times) if completion_times else float('inf')
        results.append({
            'num_peers': num_peers,
            'avg_completion_time': avg_completion,
            'stats': stats
        })
    
    return results

def run_simulation_with_varying_speeds(num_peers=10, speeds=[0.5, 1.0, 1.5, 2.0, 2.5]):
    """Run multiple simulations with different download speeds."""
    results = []
    
    for speed in speeds:
        print(f"\n=== Running simulation with speed factor {speed} ===\n")
        
        # Create event queue
        event_queue = EventQueue()
        
        # Create peers (1 seeder, rest leechers)
        peers = {}
        peers['peer1'] = Peer('peer1', is_seeder=True)
        
        for i in range(2, num_peers + 1):
            peer_id = f'peer{i}'
            peers[peer_id] = Peer(peer_id, is_seeder=False, download_speed=speed)
        
        # Create simulator
        simulator = Simulator(event_queue, peers)
        
        # Schedule initial connection events
        # Connect all leechers to the seeder
        for i in range(2, num_peers + 1):
            peer_id = f'peer{i}'
            simulator.schedule_event(
                0.1 * (i - 1),  # Stagger connections
                "CONNECT",
                {
                    'peer_id': peer_id,
                    'target_peer_id': 'peer1'
                }
            )
        
        # Also connect some peers to each other (partial mesh)
        for i in range(2, num_peers + 1, 2):
            if i + 1 <= num_peers:
                peer_id = f'peer{i}'
                target_id = f'peer{i+1}'
                simulator.schedule_event(
                    5.0 + 0.1 * (i - 1),  # Connect after initial downloads start
                    "CONNECT",
                    {
                        'peer_id': peer_id,
                        'target_peer_id': target_id
                    }
                )
        
        # Run simulation
        stats = simulator.run(max_time=100, max_events=1000)
        
        # Calculate average completion time
        completion_times = []
        for peer_id, peer_stat in stats['peer_stats'].items():
            if not peer_id == 'peer1' and peer_stat['download_complete_time'] is not None:
                completion_times.append(peer_stat['download_complete_time'])
        
        avg_completion = sum(completion_times) / len(completion_times) if completion_times else float('inf')
        results.append({
            'speed': speed,
            'avg_completion_time': avg_completion,
            'stats': stats
        })
    
    return results

def create_all_visualizations(peer_results, speed_results):
    """Create all required visualizations."""
    try:
        # Create output directory
        os.makedirs("simulation_results", exist_ok=True)
        
        # Get timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. File completion time vs. number of peers
        plt.figure(figsize=(10, 6))
        
        # Extract data
        peer_counts = [result['num_peers'] for result in peer_results]
        completion_times = [result['avg_completion_time'] for result in peer_results]
        
        plt.plot(peer_counts, completion_times, 'o-', linewidth=2, markersize=8)
        plt.title('File Completion Time vs. Number of Peers', fontsize=16)
        plt.xlabel('Number of Peers', fontsize=14)
        plt.ylabel('Average Completion Time', fontsize=14)
        plt.grid(True)
        plt.tight_layout()
        
        # Save the figure
        plt.savefig(f'simulation_results/completion_vs_peers_{timestamp}.png')
        plt.close()
        
        # Save the data as CSV
        pd.DataFrame({
            'num_peers': peer_counts,
            'avg_completion_time': completion_times
        }).to_csv(f'simulation_results/completion_vs_peers_{timestamp}.csv', index=False)
        
        print(f"Created completion vs peers graph")
        
        # 2. Number of active peers over time
        plt.figure(figsize=(10, 6))
        
        # Take the last simulation which should have the most peers
        last_sim = peer_results[-1]['stats']
        
        # Extract data
        times = [point[0] for point in last_sim['active_peers_over_time']]
        counts = [point[1] for point in last_sim['active_peers_over_time']]
        
        plt.plot(times, counts, 'o-', linewidth=2, markersize=8)
        plt.title('Active Peers Over Time', fontsize=16)
        plt.xlabel('Simulation Time', fontsize=14)
        plt.ylabel('Number of Active Peers', fontsize=14)
        plt.grid(True)
        plt.tight_layout()
        
        # Save the figure
        plt.savefig(f'simulation_results/active_peers_over_time_{timestamp}.png')
        plt.close()
        
        # Save the data as CSV
        pd.DataFrame({
            'time': times,
            'active_peers': counts
        }).to_csv(f'simulation_results/active_peers_over_time_{timestamp}.csv', index=False)
        
        print(f"Created active peers over time graph")
        
        # 3. File completion time vs. download/upload speed
        plt.figure(figsize=(10, 6))
        
        # Extract data
        speeds = [result['speed'] for result in speed_results]
        completion_times = [result['avg_completion_time'] for result in speed_results]
        
        plt.plot(speeds, completion_times, 'o-', linewidth=2, markersize=8)
        plt.title('File Completion Time vs. Download Speed', fontsize=16)
        plt.xlabel('Download Speed Factor', fontsize=14)
        plt.ylabel('Average Completion Time', fontsize=14)
        plt.grid(True)
        plt.tight_layout()
        
        # Save the figure
        plt.savefig(f'simulation_results/completion_vs_speed_{timestamp}.png')
        plt.close()
        
        # Save the data as CSV
        pd.DataFrame({
            'speed': speeds,
            'avg_completion_time': completion_times
        }).to_csv(f'simulation_results/completion_vs_speed_{timestamp}.csv', index=False)
        
        print(f"Created completion vs speed graph")
        
        # 4. Individual peer download progress
        plt.figure(figsize=(12, 8))
        
        # Take a middle simulation with moderate peers
        mid_sim = peer_results[len(peer_results)//2]['stats']
        
        # Plot each peer's piece count over time
        for peer_id, peer_stat in mid_sim['peer_stats'].items():
            if peer_id == 'peer1':
                continue  # Skip the seeder
                
            piece_data = peer_stat['piece_count_over_time']
            times = [point['time'] for point in piece_data]
            pieces = [point['pieces'] for point in piece_data]
            
            if times and pieces:
                plt.plot(times, pieces, '-', linewidth=2, label=f'Peer {peer_id}')
        
        plt.title('Peer Download Progress Over Time', fontsize=16)
        plt.xlabel('Simulation Time', fontsize=14)
        plt.ylabel('Number of Pieces', fontsize=14)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        
        # Save the figure
        plt.savefig(f'simulation_results/peer_download_progress_{timestamp}.png')
        plt.close()
        
        print(f"Created peer download progress graph")
        
        print(f"\nAll visualizations saved in simulation_results/ directory")
        
    except Exception as e:
        print(f"Error creating visualizations: {e}")
        import traceback
        traceback.print_exc()

def save_console_output(output_file):
    """
    Save all console output to a text file.
    Uses the logging module to capture both stdout and stderr.
    """
    import logging
    import sys
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Add file handler
    file_handler = logging.FileHandler(output_file, mode='w')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(file_handler)
    
    # Also add a stream handler to still see output in console
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(stream_handler)
    
    # Redirect stdout and stderr to the logger
    class LoggerWriter:
        def __init__(self, level):
            self.level = level
            self.buffer = []
            
        def write(self, message):
            if message.strip():
                self.buffer.append(message)
                if message.endswith('\n'):
                    self.flush()
                    
        def flush(self):
            if self.buffer:
                msg = ''.join(self.buffer)
                self.buffer = []
                self.level(msg.rstrip())
    
    sys.stdout = LoggerWriter(root_logger.info)
    sys.stderr = LoggerWriter(root_logger.error)
    
    print(f"Console output is being saved to {output_file}")

def save_detailed_logs(stats, log_dir):
    """
    Save detailed simulation logs as CSV files.
    """
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Overall simulation metrics
    overall_log = {
        'timestamp': [timestamp],
        'events_processed': [stats['events_processed']],
        'piece_transfers': [stats['piece_transfers']]
    }
    pd.DataFrame(overall_log).to_csv(f"{log_dir}/overall_metrics_{timestamp}.csv", index=False)
    
    # 2. Peer completion times
    peer_completion = []
    for peer_id, peer_stat in stats['peer_stats'].items():
        peer_completion.append({
            'peer_id': peer_id,
            'pieces_downloaded': peer_stat['pieces'],
            'download_complete_time': peer_stat['download_complete_time'],
            'is_complete': peer_stat['pieces'] == 10,
            'download_speed': peer_stat.get('download_speed', 1.0)
        })
    pd.DataFrame(peer_completion).to_csv(f"{log_dir}/peer_completion_{timestamp}.csv", index=False)
    
    # 3. Active peers over time
    active_peers_df = pd.DataFrame(stats['active_peers_over_time'], columns=['time', 'active_peers'])
    active_peers_df.to_csv(f"{log_dir}/active_peers_{timestamp}.csv", index=False)
    
    # 4. Individual piece arrival times for each peer
    for peer_id, peer_stat in stats['peer_stats'].items():
        piece_arrivals = []
        for piece_idx, arrival_time in peer_stat.get('piece_arrival_times', {}).items():
            piece_arrivals.append({
                'piece_index': piece_idx,
                'arrival_time': arrival_time
            })
        if piece_arrivals:
            pd.DataFrame(piece_arrivals).to_csv(
                f"{log_dir}/piece_arrivals_{peer_id}_{timestamp}.csv", index=False
            )
    
    print(f"Detailed logs saved to {log_dir}")

if __name__ == "__main__":
    # Create output directory
    os.makedirs("simulation_results", exist_ok=True)
    
    # Set up timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Start capturing console output
    save_console_output(f"simulation_results/console_output_{timestamp}.txt")
    
    print("BitTorrent Simulator with Visualizations")
    print("========================================")
    print(f"Simulation started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"All output will be saved to simulation_results/ directory")
    
    try:
        # Run simulations with varying numbers of peers
        print("\n--- Running simulations with varying numbers of peers ---")
        peer_results = run_simulation_with_varying_peers(base_peers=5, max_peers=20, step=5)
        
        # Run simulations with varying download speeds
        print("\n--- Running simulations with varying download speeds ---")
        speed_results = run_simulation_with_varying_speeds(num_peers=10, speeds=[0.5, 1.0, 1.5, 2.0, 2.5])
        
        # Create visualizations
        print("\n--- Creating visualizations ---")
        create_all_visualizations(peer_results, speed_results)
        
        # Save detailed logs of the last simulation
        print("\n--- Saving detailed logs ---")
        logs_dir = f"simulation_results/logs_{timestamp}"
        save_detailed_logs(speed_results[-1]['stats'], logs_dir)
        
        print("\nSimulation and visualization completed successfully!")
        print("Check the 'simulation_results' directory for the output files.")
        print(f"Simulation ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\nSimulation failed with error: {e}")
        import traceback
        traceback.print_exc()