from wcps_core.packets import OutPacket
from wcps_game.packets.packet_list import ClientXorKeys, PacketList

# Manual implementation of the votekick subpacket
# so that I don't have to build this one manually
# each time I need to send it to notify players about a kick


class ManualVoteKick(OutPacket):
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
        self.append(4)
        self.append(0)
        self.append(0)
        self.append(0)
        self.append(0)
        if kicked:
            self.append(75)
        else:
            self.append(0)
        self.fill(0, 4)
