from wcps_core.constants import Ports, ServerTypes

class GameServer():
    def __init__(self):
        self.name = "WCPS"
        self.ip = "127.0.0.1"
        self.port = Ports.GAME_CLIENT
        self.current_players = 0
        self.max_players = 0
        self.current_rooms = 0
        self.id = 0
        self.server_type = ServerTypes.ENTIRE