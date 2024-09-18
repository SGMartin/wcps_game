from wcps_core.constants import ErrorCodes as corerr
from wcps_core.packets import OutPacket

from wcps_game.packets.packet_list import PacketList, ClientXorKeys


class SelectChannel(OutPacket):
    def __init__(self, target_channel: int = 0):
        super().__init__(
            packet_id=PacketList.DO_SET_CHANNEL,
            xor_key=ClientXorKeys.SEND
        )
        self.append(corerr.SUCCESS)
        self.append(target_channel)
