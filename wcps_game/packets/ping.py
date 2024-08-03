from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_core.packets import OutPacket

from wcps_game.packets.packet_list import PacketList, ClientXorKeys


class Ping(OutPacket):
    def __init__(self, u: "User"):
        super().__init__(
            packet_id=PacketList.PING,
            xor_key=ClientXorKeys.SEND
        )
        self.append(5000)    # ping frequency in milliseconds
        self.append(u.ping)  # ping
        self.append(-1)      # -1 = no event, 175 = winter holidays
        self.append(100)     # event duration
        self.append(0)       # 3 exp weekend, 4 exp event, 0 = none
        self.append(1)       # exp rate
        self.append(1)       # dinar rate
        self.append(u.premium_seconds_left)   # premium time in seconds -1 = no premium
