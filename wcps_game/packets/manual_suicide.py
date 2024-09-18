from wcps_core.packets import OutPacket
from wcps_game.packets.packet_list import ClientXorKeys, PacketList

# Manual implementation of the suicide subpacket
# so that I don't have to build this one manually
# each time I need to send it


class ManualSuicide(OutPacket):
    def __init__(self, room, player, suicide_type: int, out_of_map_limits: int):
        super().__init__(
            packet_id=PacketList.DO_GAME_PROCESS,
            xor_key=ClientXorKeys.SEND
        )

        self.append(1)
        self.append(player.id)
        self.append(room.id)
        self.append(2)
        self.append(PacketList.DO_SUICIDE)
        self.append(0)
        self.append(suicide_type)

        if out_of_map_limits:
            self.append(2)
        else:
            self.append(player.id)

        self.fill(0, 7)
