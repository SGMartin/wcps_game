from wcps_core.constants import ErrorCodes as correrr
from wcps_core.packets import OutPacket

from wcps_game.packets.packet_list import ClientXorKeys, PacketList


class Explosives(OutPacket):
    def __init__(self, blocks: list, bomb_id: int = 0):
        super().__init__(
            packet_id=PacketList.DO_BOMB_PROCESS,
            xor_key=ClientXorKeys.SEND
        )
        self.append(correrr.SUCCESS)

        for idx, block in enumerate(blocks):
            if idx == 4:
                self.append(bomb_id)
            else:
                self.append(block)

        self.append(0)
