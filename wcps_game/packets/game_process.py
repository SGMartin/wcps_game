from wcps_core.packets import OutPacket
from wcps_game.packets.packet_list import ClientXorKeys, PacketList


class GameProcess(OutPacket):
    def __init__(self, blocks: list):
        super().__init__(
            packet_id=PacketList.DO_GAME_PROCESS,
            xor_key=ClientXorKeys.SEND
        )

        # For this packet we just copy all block as is, we handle packet creation
        # at the handler
        for block in blocks:
            self.append(block)
