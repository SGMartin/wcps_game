from wcps_core.packets import OutPacket
from wcps_game.config import settings
from wcps_game.game.constants import GameMode, room_time_limit_index
from wcps_game.packets.packet_list import ClientXorKeys, PacketList

# Manual implementation of the 0x34/DO_TYPE_CLICK subpacket
# so that I don't have to build this one manually
# each time I need to send the room settings


class ManualTypeClick(OutPacket):
    """DO_TYPE_CLICK 0x34 with the room's own settings. The client writes p0..p4 to its room
    data and to the OldUI room. The answer to BACK_TO_LOBBY resets both: map 0 in the room
    data, the channel default map in the OldUI room, so this one goes after it (#87)."""

    def __init__(self, room):
        super().__init__(
            packet_id=PacketList.DO_GAME_PROCESS,
            xor_key=ClientXorKeys.SEND
        )

        cqc_rounds = room.rounds_setting if room.game_mode == GameMode.EXPLOSIVE else 0
        tdm_tickets = room.tickets_setting if room.game_mode > GameMode.EXPLOSIVE else 0

        self.append(1)
        self.append(room.master_slot)
        self.append(room.id)
        self.append(2)
        self.append(PacketList.DO_TYPE_CLICK)
        self.append(1)  # b0
        self.append(0)  # ext: no extended block
        self.append(room.game_mode)  # game mode
        self.append(room.current_map)  # map
        self.append(cqc_rounds)  # explosive rounds
        self.append(tdm_tickets)  # TDM tickets and FFA kill limit
        self.append(room_time_limit_index(settings().game_time_limit))  # time limit index
        self.fill(0, 3)  # not read
