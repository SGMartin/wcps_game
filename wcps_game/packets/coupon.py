from wcps_core.packets import OutPacket
from wcps_game.packets.packet_list import PacketList, ClientXorKeys
from wcps_game.packets.error_codes import CouponError


class Coupon(OutPacket):
    def __init__(self, error_code: CouponError, awarded_dinars: int = 0):
        super().__init__(
            packet_id=PacketList.DO_COUPON,
            xor_key=ClientXorKeys.SEND
        )

        self.append(error_code)
        # Reward type (0x5f3dd0): 0 Dinar, followed by the new money total; 1 inventory string;
        # 2/3 inventory, slot string and money.
        self.append(0)
        self.append(awarded_dinars)  # new money total: the client replaces its money with it
