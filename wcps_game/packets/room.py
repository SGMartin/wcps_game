import random
import socket
import struct

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room
    from wcps_game.game.game_server import User

from wcps_core.constants import ErrorCodes as corerr
from wcps_core.packets import OutPacket

from wcps_game.game.constants import GameMode, RoomUpdateType
from wcps_game.packets.packet_list import PacketList, ClientXorKeys
from wcps_game.packets.error_codes import RoomCreateError, RoomJoinError, RoomInvitationError


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


class RoomLeave(OutPacket):
    def __init__(self, user: "User", room: "Room", old_slot: int):
        super().__init__(
            packet_id=PacketList.DO_EXIT_ROOM,
            xor_key=ClientXorKeys.SEND
        )
        self.append(corerr.SUCCESS)
        self.append(user.session_id)
        self.append(old_slot)
        self.append(room.get_player_count())
        self.append(room.master_slot)
        self.append(user.xp)
        self.append(user.money)


class RoomList(OutPacket):
    def __init__(self, room_page: int, room_list: list):
        super().__init__(
            packet_id=PacketList.DO_ROOM_LIST,
            xor_key=ClientXorKeys.SEND
        )

        self.append(len(room_list))  # The total room list for this page
        self.append(room_page)
        self.append(0)  # ?

        for room in room_list:
            add_room_info_to_packet(self, room)


class RoomInfoUpdate(OutPacket):
    def __init__(self, room_to_update: "Room", update_type: RoomUpdateType):
        super().__init__(
            packet_id=PacketList.DO_ROOM_INFO_CHANGE,
            xor_key=ClientXorKeys.SEND
        )

        self.append(room_to_update.id)

        if update_type == RoomUpdateType.DELETE:
            self.append(update_type)
        else:
            self.append(update_type)
            add_room_info_to_packet(self, room_to_update)


class RoomJoin(OutPacket):
    def __init__(self, error_code: RoomJoinError, room_to_join: "Room", player_slot: int = 0):
        super().__init__(
            packet_id=PacketList.DO_JOIN_ROOM,
            xor_key=ClientXorKeys.SEND
        )

        if room_to_join is None:
            self.append(error_code)
        else:
            self.append(corerr.SUCCESS)
            self.append(player_slot)
            add_room_info_to_packet(self, room_to_join)


class RoomInvite(OutPacket):
    def __init__(self, error_code: RoomInvitationError, user: "User" = None, message: str = ""):
        super().__init__(
            packet_id=PacketList.DO_INVITATION,
            xor_key=ClientXorKeys.SEND
        )
        if error_code != corerr.SUCCESS or user is None:
            self.append(error_code)
        else:
            self.append(corerr.SUCCESS)
            self.append(0)
            self.append(-1)
            self.append(user.session_id)
            self.append(user.session_id)  # ping?
            self.append(user.displayname)
            self.fill(-1, 4)  # Clan blocks
            self.append(1)
            self.append(18)
            self.append(user.xp)
            self.append(3)  # ??
            self.append(0)
            self.append(-1)
            self.append(message)
            self.append(user.room.id)
            self.append(user.room.password)


class RoomKick(OutPacket):
    def __init__(self, target_player: int):
        super().__init__(
            packet_id=PacketList.DO_EXPEL_PLAYER,
            xor_key=ClientXorKeys.SEND
        )

        self.append(corerr.SUCCESS)
        self.append(target_player)


class RoomPlayers(OutPacket):
    def __init__(self, player_list: list):
        super().__init__(
            packet_id=PacketList.DO_GAME_USER_LIST,
            xor_key=ClientXorKeys.SEND
        )

        self.append(len(player_list))  # How many players are in the room

        for player in player_list:
            self.append(player.user.session_id)  # Should be user id TODO: check if session id works
            self.append(player.user.session_id)
            self.append(player.id)  # The slot in the room
            self.append(player.ready)  # Ready or not
            self.append(player.team)
            self.append(player.weapon)
            self.append(0)  # Unknown
            self.append(player.branch)  # Engineer, medic etc.
            self.append(player.health)
            self.append(player.user.displayname)
            self.fill(-1, 3)  # Clan blocks here: ID/NAME/RANK
            self.append(1)  # Unknown
            self.append(0)  # Unknown
            self.append(910)  # Unknown. The client send this on request time. Client ver???
            # 910 (Always)? Send From Login (910 G1, 410 NX , 300 KR , 100 PH, INVALID TW)
            self.append(player.user.premium)
            self.append(-1)  # Unknown? Possible smile badge
            self.append(player.user.stats.kills)
            self.append(player.user.stats.deaths)
            self.append(random.randint(0, 149))  # random [0, 149] unknown
            self.append(player.user.xp)
            self.append(player.vehicle_id)
            self.append(player.vehicle_seat)
            # Connection data here for UDP
            self.append(ip_string_to_long(player.user.remote_end_point[0]))
            self.append(player.user.remote_port)
            self.append(ip_string_to_long(player.user.local_end_point[0]))
            self.append(player.user.local_port)
            self.append(0)  # Unknown


def add_room_info_to_packet(packet: OutPacket, room):
    cqc_rounds = room.rounds_setting if room.game_mode == GameMode.EXPLOSIVE else 0
    tdm_tickets = room.tickets_setting if room.game_mode > GameMode.EXPLOSIVE else 0

    packet.append(room.id)
    packet.append(1)  # Unknown
    packet.append(room.state)
    packet.append(room.master_slot)
    packet.append(room.displayname)
    packet.append(room.password_protected)
    packet.append(room.max_players)
    packet.append(room.get_player_count())
    packet.append(room.current_map)
    packet.append(cqc_rounds)  # Explosive rounds when game mode is explosives/mission
    packet.append(tdm_tickets)  # TDM tickets and FFA rounds
    packet.append(0)  # Unknown
    packet.append(room.game_mode)  # game mode
    packet.append(4)  # Unknown
    packet.append(1)  # #TODO: Can join?
    packet.append(0)  # ??
    packet.append(room.supermaster)
    packet.append(room.type)  # Unused in Chapter 1
    packet.append(room.level_limit)
    packet.append(room.premium_only)
    packet.append(room.enable_votekick)
    packet.append(room.autostart)  # autostart
    packet.append(0)  # average ping before patch G1-17
    packet.append(room.ping_limit)  # ping limit
    packet.append(-1)  # Is clan war? possibly incomplete? if enabled needs 2 blocks more


def ip_string_to_long(ip_addr: str):
    packed_ip = socket.inet_aton(ip_addr)
    ip_as_long = struct.unpack("<I", packed_ip)[0]
    return ip_as_long
