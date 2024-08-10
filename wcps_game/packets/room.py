from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room

from wcps_core.constants import ErrorCodes as corerr
from wcps_core.packets import OutPacket

# from wcps_game.game.constants import GameMode
from wcps_game.packets.packet_list import PacketList, ClientXorKeys
from wcps_game.packets.error_codes import RoomCreateError


class RoomCreate(OutPacket):
    def __init__(self, error_code: RoomCreateError, new_room: "Room" = None):
        super().__init__(
            packet_id=PacketList.ROOM_CREATE,
            xor_key=ClientXorKeys.SEND
        )

        if error_code != corerr.SUCCESS or new_room is None:
            self.append(error_code)
        else:
            self.append(corerr.SUCCESS)
            self.append(0)  # ?
            add_room_info_to_packet(self, new_room)


def add_room_info_to_packet(packet: OutPacket, room):
    # cqc_rounds = room.rounds_setting if room.game_mode == GameMode.EXPLOSIVE else 0
    # tdm_tickets = room.tickets_setting if room.game_mode > GameMode.EXPLOSIVE else 0

    packet.append(room.id)
    packet.append(1)  # Unknown
    packet.append(room.state)
    packet.append(room.master_slot)
    packet.append(room.displayname)
    packet.append(room.password_protected)
    packet.append(room.max_players)
    packet.append(1)  # TODO: player count update here
    packet.append(12)  # TODO: current map update here
    packet.append(room.rounds_setting)  # Explosive rounds when game mode is explosives/mission
    packet.append(room.tickets_setting)  # TDM tickets and FFA rounds
    packet.append(0)  # Unknown
    packet.append(room.game_mode)  # game mode
    packet.append(4)  # Unknown
    packet.append(1)  # Can join?
    packet.append(0)  # ??
    packet.append(room.supermaster)
    packet.append(room.type)  # Unused in Chapter 1
    packet.append(room.level_limit)
    packet.append(room.premium_only)
    packet.append(room.vote_kick)
    packet.append(room.autostart)  # autostart
    packet.append(0)  # average ping before patch G1-17
    packet.append(room.ping_limit)  # ping limit
    packet.append(-1)  # Is clan war? possibly incomplete? if enabled needs 2 blocks more
