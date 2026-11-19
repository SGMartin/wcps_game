from wcps_core.packets import OutPacket
from wcps_game.game.constants import DeathCause
from wcps_game.packets.packet_list import ClientXorKeys, PacketList

# Manual implementation of the suicide subpacket
# so that I don't have to build this one manually
# each time I need to send it


class ManualSuicide(OutPacket):
    """DO_SUICIDE 0x9d sent by the server. The client (PF23 0x4e6d70) kills the sender slot (the player) and
    shows the message of p1 (DeathCause). The cause used to go in ext, so the client always read p1 = 0
    and showed "Suicide"."""

    def __init__(self, room, player, suicide_type: int, out_of_map_limits: int):
        super().__init__(
            packet_id=PacketList.DO_GAME_PROCESS,
            xor_key=ClientXorKeys.SEND
        )

        if out_of_map_limits:
            suicide_type = DeathCause.MINE  # the danger zone death

        self.append(1)
        self.append(player.id)
        self.append(room.id)
        self.append(2)
        self.append(PacketList.DO_SUICIDE)
        self.append(0)  # b0
        self.append(0)  # ext: no extended block
        self.append(0)  # p0
        self.append(suicide_type)  # p1: cause
        self.fill(0, 6)  # p2..p7
