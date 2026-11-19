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
        self.append(0)  # b0
        self.append(0)  # ext: no extended block (it was 1 with nothing after it)
        self.append(3)  # p0: spawn protection in seconds (the character blinks), overrides the room value
        self.append(363)  # p1: only written to a client debug log
        self.append(0)  # p2: side of the first half of the slots
        self.append(1)  # p3: side of the second half of the slots
        self.fill(0, 4)  # p4..p7, not read
