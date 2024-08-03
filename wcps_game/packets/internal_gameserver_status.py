import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import GameServer

from wcps_core.constants import ErrorCodes, InternalKeys
from wcps_core.packets import OutPacket

from wcps_game.packets.packet_list import PacketList


class GameServerStatus(OutPacket):
    def __init__(self, server: "GameServer" = None):
        super().__init__(
            packet_id=PacketList.INTERNAL_GAME_AUTHENTICATION,
            xor_key=InternalKeys.XOR_GAME_SEND
        )

        self.append(ErrorCodes.SUCCESS)
        self.append(int(time.time()))
        self.append(server.id)  # current server id
        self.append(server.get_player_count())  # current server pop
        self.append(server.current_rooms)  # current room pop
