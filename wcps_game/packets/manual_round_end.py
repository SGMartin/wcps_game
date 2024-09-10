from wcps_core.packets import OutPacket
from wcps_game.packets.packet_list import ClientXorKeys, PacketList

# Manual implementation of the 0x6/DO_ROUND_END subpacket
# so that I don't have to build this one manually
# each time I need to send it for explosive


class ManualRoundEnd(OutPacket):
    def __init__(self, room, winning_team):
        super().__init__(
            packet_id=PacketList.DO_GAME_PROCESS,
            xor_key=ClientXorKeys.SEND
        )

        self.append(1)
        self.append(-1)
        self.append(room.id)
        self.append(1)
        self.append(PacketList.DO_ROUND_END)
        self.append(0)
        self.append(1)
        self.append(winning_team)  # Might be for the scoreboard
        self.append(room.current_game_mode.current_round_derbaran())
        self.append(room.current_game_mode.current_round_niu())
        self.append(5)  # rounds remaining???
        self.append(0)
        self.append(92)  # WTF
        self.append(-1)
        self.append(0)
        self.append(0)
        self.append(1200000)
        self.append(-900000)
        self.append(1200000)
        self.append("0.0000")
        self.append("0.0000")
        self.append("0.0000")
        self.append("0.0000")
        self.append("0.0000")
        self.append("0.0000")
        self.append(0)
        self.append(0)
        self.append("DS05")
