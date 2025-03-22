from utils.configs import Configs
from network.peer import Peer
from core.event_queue import EventQueue
from core.simulator import Simulator

def main():
    # Parse configs
    config = Configs('config/common.cfg', 'config/peer_info.cfg')
    print(config)
    
    # Create peers
    peers = {}
    for (peer_id, host, port) in config.peer_info:
        p = Peer(peer_id, host, port, config)
        peers[peer_id] = p

    # Create event queue and simulator
    event_queue = EventQueue()
    sim = Simulator(event_queue, peers)

    # Example: schedule a simple event
    # e.g., at time=10, generate a "connect" event for peer 1001 to connect to peer 1002
    sim.schedule_event(10, "CONNECT_PEER", {'peer_id': '1001', 'target_peer_id': '1002'})

    # Start the simulator
    sim.run(end_time=100)
    
    # The actual event logic (CONNECT_PEER) would be handled inside `dispatch_event`,
    # or inside `process_event` in the Peer. You’d likely expand that logic 
    # to call `connect_to_peer(...)`.

if __name__ == "__main__":
    main()
