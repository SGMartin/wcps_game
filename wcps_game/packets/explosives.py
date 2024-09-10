from wcps_core.constants import ErrorCodes as correrr
from wcps_core.packets import OutPacket

from wcps_game.packets.packet_list import ClientXorKeys, PacketList


class Explosives(OutPacket):
    def __init__(self, blocks: list):
        super().__init__(
            packet_id=PacketList.DO_BOMB_PROCESS,
            xor_key=ClientXorKeys.SEND
        )
        self.append(correrr.SUCCESS)

        for block in blocks:
            self.append(block)

        self.append(0)
