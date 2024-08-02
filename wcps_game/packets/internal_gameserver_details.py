from wcps_core.constants import ErrorCodes, InternalKeys
from wcps_core.packets import OutPacket

from wcps_auth.packets.packet_list import PacketList


class GameServerAuthentication(OutPacket):
    def __init__(self, server: None):
        super().__init__(
            packet_id=PacketList.INTERNAL_GAME_AUTHENTICATION,
            xor_key=InternalKeys.XOR_GAME_SEND
        )

        self.append(ErrorCodes.SUCCESS)
        self.append(server.id)  # Server ID
        self.append(server.name)  # Server name
        self.append(server.ip)
        self.append(server.port)
        self.append(server.server_type)  # type
        self.append(server.get_player_count())  # curr pop
        self.append(server.max_players)  # max pop
