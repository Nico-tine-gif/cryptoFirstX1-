from .peer import Peer


class PeerRegistry:

    def __init__(self):
        self.peers = {}

    def add(self, peer: Peer):
        self.peers[peer.peer_id] = peer

    def remove(self, peer_id: str):
        self.peers.pop(peer_id, None)

    def all(self):
        return list(self.peers.values())
