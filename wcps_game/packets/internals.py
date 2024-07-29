import time
from typing import TYPE_CHECKING

from wcps_core.constants import InternalKeys, ErrorCodes
from wcps_core.packets import OutPacket
from wcps_core.packets import PacketList as corepackets

if TYPE_CHECKING:
    from game.game_server import GameServer, User

class GameServerDetails(OutPacket):
    def __init__(self, this_server: 'GameServer'):
        super().__init__(
            packet_id=corepackets.GameServerAuthentication,
            xor_key=InternalKeys.XOR_GAME_SEND
        )

        self.append(ErrorCodes.SUCCESS)
        self.append(this_server.id)  # Server ID
        self.append(this_server.name)  # Server name
        self.append(this_server.ip)
        self.append(this_server.port)
        self.append(this_server.server_type)  # type
        self.append(this_server.current_players)  # curr pop
        self.append(this_server.max_players)  # max pop

class GameServerStatus(OutPacket):
    def __init__(self, this_server: 'GameServer'):
        super().__init__(
            packet_id=corepackets.GameServerStatus,
            xor_key=InternalKeys.XOR_GAME_SEND
        )

        self.append(ErrorCodes.SUCCESS)
        self.append(int(time.time()))
        self.append(this_server.id)  # current server id
        self.append(this_server.current_players)  # current server pop
        self.append(this_server.current_rooms)  # current room pop

class InternalPlayerAuthorization(OutPacket):
    def __init__(self, error_code:ErrorCodes, u:"User"):
        super().__init__(
            packet_id=corepackets.ClientAuthentication,
            xor_key=InternalKeys.XOR_GAME_SEND
        )

        self.append(error_code)
        if error_code == ErrorCodes.UPDATE or error_code.END_CONNECTION:
            self.append(u.session_id)
        else:
            self.append(u.session_id)
            self.Append(u.username)
            self.append(u.rights)
