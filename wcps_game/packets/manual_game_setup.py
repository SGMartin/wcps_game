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
        # p0: spawn protection in seconds, overrides the room value; counted down per frame, the
        # character blinks while it lasts (PF23 0x4e2a9e, 0x4f264c, 0x4fa693)
        self.append(3)
        self.append(363)  # p1: only formatted into a debug string nothing reads (PF23 0x4e2c4f)
        # p2/p3: in-game side of the slots below / from max_players / 2 (PF23 0x4e29d0). Used for spawn
        # points, the explosive mission text and ROUND_END. Game mode 1 can set every side to 0.
        self.append(0)  # p2
        self.append(1)  # p3
        self.fill(0, 4)  # p4..p7, not read
