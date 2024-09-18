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
        self.append(0)  # ?
        self.append(awarded_dinars)
