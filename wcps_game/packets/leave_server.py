from wcps_core.constants import ErrorCodes
from wcps_core.packets import OutPacket

from wcps_game.packets.packet_list import PacketList, ClientXorKeys


class LeaveServer(OutPacket):
    def __init__(self):
        super().__init__(
            packet_id=PacketList.LeaveServer,
            xor_key=ClientXorKeys.SEND
        )
        self.append(ErrorCodes.SUCCESS)
