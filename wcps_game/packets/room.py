import random
import socket
import struct

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room
    from wcps_game.game.game_server import User

from wcps_core.constants import ErrorCodes as corerr
from wcps_core.packets import OutPacket

from wcps_game.config import settings
from wcps_game.game.constants import GameMode, RoomUpdateType, room_time_limit_index
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
            self.append(0)  # own slot in the room
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
    # Built per user: 'can join' depends on who receives it
    def __init__(self, room_page: int, room_list: list, viewer: "User"):
        super().__init__(
            packet_id=PacketList.DO_ROOM_LIST,
            xor_key=ClientXorKeys.SEND
        )

        self.append(len(room_list))  # The total room list for this page
        self.append(room_page)
        self.append(0)  # if non-zero, one client list mode fills the page in reverse order

        for room in room_list:
            add_room_info_to_packet(self, room, viewer)


class RoomInfoUpdate(OutPacket):
    # Built per user: 'can join' depends on who receives it
    def __init__(self, room_to_update: "Room", update_type: RoomUpdateType, viewer: "User"):
        super().__init__(
            packet_id=PacketList.DO_ROOM_INFO_CHANGE,
            xor_key=ClientXorKeys.SEND
        )

        self.append(room_to_update.id)

        if update_type == RoomUpdateType.DELETE:
            self.append(update_type)
        else:
            self.append(update_type)
            add_room_info_to_packet(self, room_to_update, viewer)


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


class RoomSpectate(OutPacket):
    def __init__(self, room_to_join: "Room" = None, spectate_slot: int = 0):
        super().__init__(
            packet_id=PacketList.DO_GUEST_JOIN,
            xor_key=ClientXorKeys.SEND
        )

        self.append(corerr.SUCCESS)
        if room_to_join is None:
            # Leave confirmation. The client reads <code> <join/leave> and on leave
            # clears its spectator flag and goes back to the lobby.
            self.append(0)
            return

        self.append(1)
        self.append(spectate_slot)
        add_room_info_to_packet(self, room_to_join)


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
            self.append(0)  # stored as a flag (== 1), no client reader found
            self.append(player.branch)  # Engineer, medic etc.
            self.append(player.health)
            self.append(player.user.displayname)
            self.fill(-1, 3)  # Clan blocks here: ID/NAME/RANK, all read as ints
            self.append(1)  # short, no client reader found
            self.append(0)  # short, no client reader found
            self.append(910)  # short, only shown by a debug overlay as "<nick> <value>"
            # 910 (Always)? Send From Login (910 G1, 410 NX , 300 KR , 100 PH, INVALID TW)
            self.append(player.user.premium)
            self.append(-1)  # if 1, the results screen draws a 26x20 icon by the player
            self.append(player.user.stats.kills)
            self.append(player.user.stats.deaths)
            self.append(random.randint(0, 149))  # random [0, 149]; stored, no client reader found
            self.append(player.user.xp)
            self.append(player.vehicle_id)
            self.append(player.vehicle_seat)
            # Connection data here for UDP
            self.append(ip_string_to_long(player.user.remote_end_point[0]))
            self.append(player.user.remote_port)
            self.append(ip_string_to_long(player.user.local_end_point[0]))
            self.append(player.user.local_port)
            self.append(0)  # stored as a flag (!= 0), no client reader found


class RoomSpectators(OutPacket):
    """DO_GAME_GUEST_LIST, sent to the players of the room.

    <code> <mode> then, per spectator: <guest index> <id> <session> <nick> <notice>
    and, when adding, the UDP endpoints and a flag. Mode 0 removes the spectator from
    the peer table, 1 adds one, any other value is a count followed by that many
    entries. The client stores the spectator in peer slot guest index + 32.
    """

    def __init__(self, spec: "User", slot: int, joined: bool = True):
        super().__init__(
            packet_id=PacketList.DO_GAME_GUEST_LIST,
            xor_key=ClientXorKeys.SEND
        )
        self.append(corerr.SUCCESS)
        self.append(1 if joined else 0)
        self.append(slot - 32)  # guest index 0-4
        self.append(spec.session_id)
        self.append(spec.session_id)
        self.append(spec.displayname)
        # Only 3 makes players store a "%s is spectating" notice (never drawn in PF23)
        self.append(999)
        if not joined:
            return
        self.append(ip_string_to_long(spec.remote_end_point[0]))
        self.append(spec.remote_port)
        self.append(ip_string_to_long(spec.local_end_point[0]))
        self.append(spec.local_port)
        self.append(0)


def add_room_info_to_packet(packet: OutPacket, room, viewer: "User" = None):
    # viewer: the lobby user the room list entry is for. None for the packets sent to the room's own
    # players (create, join, spectate), where 'can join' does not matter.
    cqc_rounds = room.rounds_setting if room.game_mode == GameMode.EXPLOSIVE else 0
    tdm_tickets = room.tickets_setting if room.game_mode > GameMode.EXPLOSIVE else 0

    packet.append(room.id)
    packet.append(1)  # stored, no client reader found
    packet.append(room.lobby_state)  # Playing until every player is back from the results screen
    packet.append(room.master_slot)
    packet.append(room.displayname)
    packet.append(room.password_protected)
    packet.append(room.max_players)
    packet.append(room.get_player_count())
    packet.append(room.current_map)
    packet.append(cqc_rounds)  # Explosive rounds when game mode is explosives/mission
    packet.append(tdm_tickets)  # TDM tickets and FFA rounds
    packet.append(room_time_limit_index(settings().game_time_limit))  # time limit index (was 0 = 1 minute)
    packet.append(room.game_mode)  # game mode
    packet.append(4)  # spawn protection in seconds; DO_GO p0 overrides it
    packet.append(1 if viewer is None or room.can_join(viewer) else 0)  # can join (greyed out if 0)
    packet.append(0)  # stored, no client reader found
    packet.append(room.supermaster)
    packet.append(room.type)  # Unused in Chapter 1
    packet.append(room.level_limit)
    packet.append(room.premium_only)
    packet.append(room.enable_votekick)
    packet.append(room.autostart)  # autostart
    packet.append(0)  # room ping: the PF20/PF23 clients no longer draw it
    packet.append(room.ping_limit)  # ping limit
    # Clan war: read as a string and parsed with _atoi64; if > 0 the client reads two more ints
    packet.append(-1)


def ip_string_to_long(ip_addr: str):
    packed_ip = socket.inet_aton(ip_addr)
    ip_as_long = struct.unpack("<I", packed_ip)[0]
    return ip_as_long
