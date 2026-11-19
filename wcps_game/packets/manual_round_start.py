from wcps_core.packets import OutPacket
from wcps_game.packets.packet_list import ClientXorKeys, PacketList

# Manual implementation of the 0x5/DO_ROUND_START subpacket
# so that I don't have to build this one manually
# each time I need to send it for explosive


class ManualRoundStart(OutPacket):
    """The client (PF23 0x5f5bd0, case 5) reads p0: the winner of the round just played, compared with the
    local side to replay the round result sound (0xd2 as ROUND_END) and shown as ROUND_END's p0; p1 and p2:
    Derbaran and NIU rounds won. The old layout (from the 2018 C# server) was two fields off: Derbaran
    rounds in ext, NIU rounds in p0."""

    def __init__(self, room):
        super().__init__(
            packet_id=PacketList.DO_GAME_PROCESS,
            xor_key=ClientXorKeys.SEND
        )

        self.append(1)
        self.append(-1)
        self.append(room.id)
        self.append(1)
        self.append(PacketList.DO_ROUND_START)
        self.append(0)  # b0
        self.append(0)  # ext: no extended block
        self.append(room.current_game_mode.last_round_winner)  # p0
        self.append(room.current_game_mode.current_round_derbaran())  # p1
        self.append(room.current_game_mode.current_round_niu())  # p2
        self.fill(0, 5)  # p3..p7, not read
