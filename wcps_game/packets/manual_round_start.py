from wcps_core.packets import OutPacket
from wcps_game.packets.packet_list import ClientXorKeys, PacketList

# Manual implementation of the 0x5/DO_ROUND_START subpacket
# so that I don't have to build this one manually
# each time I need to send it for explosive


class ManualRoundStart(OutPacket):
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
        self.append(0)
        self.append(room.current_game_mode.current_round_derbaran())
        self.append(room.current_game_mode.current_round_niu())
        self.append(1)  # Unknown
        self.append(0)
        self.append(5)  # ??
        self.append(0)
        self.append(0)
        self.append(-1)
        self.append(0)
        self.append(0)
        self.append(800000)
        self.append(-184460)
        self.append(800000)
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
        self.append("DS05")  # WTF WarRock??
