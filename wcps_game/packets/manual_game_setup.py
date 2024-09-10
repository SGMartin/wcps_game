from wcps_core.packets import OutPacket
from wcps_game.packets.packet_list import ClientXorKeys, PacketList

# Manual implementation of the DO_GO subpacket
# so that I don't have to build this one manually
# each time I need to send a new DO_GO packet
# for CQC


class ManualGameSetup(OutPacket):
    def __init__(self, room):
        super().__init__(
            packet_id=PacketList.DO_GAME_PROCESS,
            xor_key=ClientXorKeys.SEND
        )

        self.append(1)
        self.append(-1)
        self.append(room.id)
        self.append(2)
        self.append(PacketList.DO_GO)
        self.append(0)
        self.append(1)
        self.append(3)  # Unknown. Some game mode shit?
        self.append(363)  # Unknown
        self.append(0)
        self.append(1)
        self.fill(0, 4)  # Unknown
