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
        # Message format: 0 = rank and grade from the XP below; any other value reads the level as a rank index
        # (0..17), so the room slot used here showed an unknown rank from level 18 on
        self.append(0)
        self.append(0)
        self.append(get_level_for_exp(user.xp))
        self.append(user.xp)
        self.append(money_earned)
