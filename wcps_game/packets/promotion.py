from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_core.packets import OutPacket

from wcps_game.game.constants import get_level_for_exp
from wcps_game.packets.packet_list import PacketList, ClientXorKeys


class Promotion(OutPacket):
    def __init__(self, user: "User", money_earned: int):
        super().__init__(
            packet_id=PacketList.DO_PROMOTION_OLD,
            xor_key=ClientXorKeys.SEND
        )
        self.append(user.room_slot)
        self.append(0)
        self.append(get_level_for_exp(user.xp))
        self.append(user.xp)
        self.append(money_earned)
