from wcps_core.packets import OutPacket
from wcps_game.packets.packet_list import ClientXorKeys, PacketList

# Manual implementation of the votekick subpacket
# so that I don't have to build this one manually
# each time I need to send it to notify players about a kick


class ManualVoteKick(OutPacket):
    """Vote kick result. The client (PF23 0x4e76e0, PF20 0x4e83b0) reads p0 = 2 as the result, p1 = target
    and compares p3 with a threshold of 80 (60 in CQC) to show the kick. The old layout (b0 = 4, p0 = 0,
    p1 = 0, p3 = 75) read as "vote state 0, target slot 0": the HUD closed but no result was shown."""

    def __init__(self, room, voted_player_id: int, kicked: bool):
        super().__init__(
            packet_id=PacketList.DO_GAME_PROCESS,
            xor_key=ClientXorKeys.SEND
        )

        self.append(1)
        self.append(-1)
        self.append(room.id)
        self.append(2)
        self.append(PacketList.DO_VOTE_KICK)
        self.append(1)  # b0
        self.append(0)  # ext: no extended block
        self.append(2)  # p0: result
        self.append(voted_player_id)  # p1: target slot
        self.append(0)  # p2
        self.append(100 if kicked else 0)  # p3: percentage, above the client threshold when kicked
        self.fill(0, 4)  # p4..p7
