import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_core.constants import ErrorCodes as corerr

import wcps_game.game.constants as gconstants

from wcps_game.game.rooms import Room
from wcps_game.handlers.packet_handler import PacketHandler
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.error_codes import (
    RoomCreateError,
    RoomJoinError,
    RoomInvitationError,
)

# Default room names of the PF20 client (m727-m729 of each textdata file) and the
# encoding of that file. Packets are read as latin-1 with spaces sent as 0x1d, so the
# names are turned into that form once here.
_DEFAULT_ROOM_NAMES = {
    "cp1252": ("Let's play WarRock today!!!", "One Shot, One Kill", "Go! Go! Go!"),
    "cp949": ("오늘도 워록 한판!", "원샷원킬", "작전지역으로 출발"),
}
DEFAULT_ROOM_NAMES = frozenset(
    name.encode(encoding).decode("latin-1").replace(" ", "\x1d")
    for encoding, names in _DEFAULT_ROOM_NAMES.items()
    for name in names
)


class RoomCreateHandler(PacketHandler):
    async def process(self, user: "User"):
        # Check and reserve with no await in between (see User.joining_room)
        if not user.authorized or user.room is not None or user.joining_room:
            return

        user.joining_room = True
        try:
            await self.create_room(user)
        finally:
            user.joining_room = False

    async def create_room(self, user: "User"):
        # bytearray(b'50910153 29440 Mediavida 1 hello 1 12 0 0 0 3 1 1 \n')

        room_name = self.get_block(0)
        has_password = bool(int(self.get_block(1)))
        input_password = self.get_block(2)
        player_limit = int(self.get_block(3))
        # map_id = int(self.get_block(4))  # Defaults to mode default. We will sanitize it anyway

        # Blocks 5 and 6 I have no idea... Friendly fire?
        unused_type = int(self.get_block(7))
        level_limit = int(self.get_block(8))
        premium_only = bool(int(self.get_block(9)))
        votekick_enabled = bool(int(self.get_block(10)))

        # Era conventions (PF20): the create room window gives a random default name
        # (in the client's language) and only lets Silver and up edit it or make the
        # room private; Bronze and up may mark it premium only (0x562c20 in the PF20
        # exe). The client already blocks the rest, so this is a defensive check.
        # PF20 only: Code Name Legacy frees these options.
        if user.premium < gconstants.Premium.SILVER and (
            room_name not in DEFAULT_ROOM_NAMES or has_password
        ):
            await self.send_generic_error(user)
            return

        if user.premium < gconstants.Premium.BRONZE and premium_only:
            await self.send_generic_error(user)
            return

        # Start validating the room name
        default_longest_name = "Let's\x1dplay\x1dWarRock\x1dtoday!!!"

        if len(room_name) not in range(0, 26) and room_name != default_longest_name:
            await self.send_generic_error(user)
            return

        # Validate password
        if has_password and (
            len(input_password) not in range(1, 11) or input_password == "NULL"
        ):
            await self.send_generic_error(user)
            return

        # Validate max players
        # 8/16/20/24/32 in CP 1 :)
        # 0/1/2/3/4

        max_players_for_room = len(
            gconstants.RoomMaximumPlayers.MAXIMUM_PLAYERS[user.channel]
        )

        if player_limit < 0 or player_limit >= max_players_for_room:
            await self.send_generic_error(user)
            return

        # Validate minimum level requirements
        this_player_level = gconstants.get_level_for_exp(user.xp)
        requested_limit = gconstants.RoomLevelLimits.MIN_LEVEL_REQUIREMENTS.get(
            level_limit
        )

        if requested_limit is None or this_player_level not in requested_limit:
            level_error = PacketFactory.create_packet(
                packet_id=PacketList.ROOM_CREATE,
                error_code=RoomCreateError.UNSUITABLE_LEVEL,
            )
            await user.send(level_error.build())
            return

        has_super_master = user.inventory.has_item("CC02")

        if not has_super_master and not votekick_enabled:
            # TODO error here. Only supermasters can disable votekick
            await self.send_generic_error(user)
            return

        # If we arrive here, it's time to start the room if any slot is available
        new_room = Room(
            master=user,
            displayname=room_name,
            password_protected=has_password,
            password=input_password,
            max_players=player_limit,
            room_type=unused_type,
            level_limit=level_limit,
            premium_only=premium_only,
            vote_kick=votekick_enabled,
            is_clanwar=False,  # TODO: investigate it in the future
        )

        this_channel = user.this_server.channels[user.channel]
        new_room_id = await this_channel.add_room(new_room)

        if new_room_id is None:
            too_many_rooms = PacketFactory.create_packet(
                packet_id=PacketList.ROOM_CREATE,
                error_code=RoomCreateError.MAX_ROOM_LIMIT,
            )
            await user.send(too_many_rooms.build())
            return

        new_room.authorize(room_id=new_room_id)

        room_create_packet = PacketFactory.create_packet(
            packet_id=PacketList.ROOM_CREATE,
            error_code=corerr.SUCCESS,
            new_room=new_room,
        )

        # The master user has been notified
        await user.send(room_create_packet.build())

        # Send the master their own updated room data (k:d, endpoint)
        # The master is always the 0 slot when the room is just created
        room_players = PacketFactory.create_packet(
            packet_id=PacketList.DO_GAME_USER_LIST, player_list=[new_room.players[0]]
        )
        await user.send(room_players.build())

        # Notify the rest of the lobby
        channel_users = await user.this_server.channels[user.channel].get_users()

        for user_to_update in channel_users:
            if user_to_update.room is None and user_to_update.room_page == new_room.room_page:
                update_packet = PacketFactory.create_packet(
                    packet_id=PacketList.DO_ROOM_INFO_CHANGE,
                    room_to_update=new_room,
                    update_type=gconstants.RoomUpdateType.CREATE,
                    viewer=user_to_update,
                )
                await user_to_update.send(update_packet.build())

    async def send_generic_error(user: "User"):
        error_packet = PacketFactory.create_packet(
            packet_id=PacketList.ROOM_CREATE, error_code=RoomCreateError.GENERIC
        )
        await user.send(error_packet.build())


class RoomJoinHandler(PacketHandler):
    async def process(self, user: "User"):
        # Check and reserve with no await in between (see User.joining_room)
        if not user.authorized or user.room is not None or user.joining_room:
            return

        user.joining_room = True
        try:
            await self.join_room(user)
        finally:
            user.joining_room = False

    async def join_room(self, user: "User"):

        room_target = int(self.get_block(0))
        room_password = self.get_block(1)

        # Target room not found
        if user.this_server.channels[user.channel].rooms[room_target] is None:
            generic_err = PacketFactory.create_packet(
                packet_id=PacketList.DO_JOIN_ROOM,
                error_code=RoomJoinError.GENERIC,
                room_to_join=None,
            )
            await user.send(generic_err.build())
            return

        this_room = user.this_server.channels[user.channel].rooms[room_target]

        # Password protected and incorrect password
        if this_room.password_protected and this_room.password != room_password:
            password_incorrect = PacketFactory.create_packet(
                packet_id=PacketList.DO_JOIN_ROOM,
                error_code=RoomJoinError.INVALID_PASSWORD,
                room_to_join=None,
            )
            await user.send(password_incorrect.build())
            return

        # Premium only, level, voted out, ping limit. The OldUI room list lets the user try to join
        # a greyed out room (no check on 'can join' before sending the join), so check it here too
        join_error = this_room.join_error(user)
        if join_error != corerr.SUCCESS:
            cannot_join = PacketFactory.create_packet(
                packet_id=PacketList.DO_JOIN_ROOM,
                error_code=join_error,
                room_to_join=None,
            )
            await user.send(cannot_join.build())
            return

        # If this function does not return none, it will send the room join packet
        player = await this_room.add_player(user)

        # Full or closed (user limit) room: both are m14 "Users exceeded for this room" in the client
        if player is None:
            room_full_error = PacketFactory.create_packet(
                packet_id=PacketList.DO_JOIN_ROOM,
                error_code=RoomJoinError.MAX_USERS,
                room_to_join=None,
            )
            await user.send(room_full_error.build())


class RoomQuickJoinHandler(PacketHandler):
    async def process(self, user: "User"):
        # Check and reserve with no await in between (see User.joining_room)
        if not user.authorized or user.room is not None or user.joining_room:
            return

        user.joining_room = True
        try:
            await self.quick_join(user)
        finally:
            user.joining_room = False

    async def quick_join(self, user: "User"):

        this_channel = user.this_server.channels[user.channel]

        for room_id, room in this_channel.rooms.items():
            if not room:
                continue

            # Room is full
            if room.get_player_count() >= room.max_players:
                continue

            # Fixed user limit
            if room.user_limit:
                continue

            # No password rooms
            if room.password_protected:
                continue

            # Premium only, level, voted out, ping limit
            if room.join_error(user) != corerr.SUCCESS:
                continue

            success = await room.add_player(user)

            if not success:
                continue

            break  # joined: do not keep adding the user to the next rooms

            # TODO: any kind of message if failed to join any room?


class RoomLeaveHandler(PacketHandler):
    async def process(self, user: "User"):

        if not user.authorized:
            return

        if user.room is not None:
            room_left = user.room
            this_room_page = room_left.room_page
            is_last_player = room_left.get_player_count() == 1

            await room_left.remove_player(user)
            user.set_room(None, 0)

            channel_users = await user.this_server.channels[user.channel].get_users()

            # Send the user the userlist
            await user.this_server.channels[user.channel].send_user_list(user, channel_users)

            # Send the user the room list
            await user.this_server.channels[user.channel].send_room_list(user)

            # Send an userlist packet for all users in the user list for their current page
            # TODO: check if packet DO_USERLIST_CHANGE (0x7110) would work here?
            # TODO: IS this really necessary? He has not left the channel...
            for c_user in channel_users:
                if c_user.room is None:
                    await user.this_server.channels[user.channel].send_user_list(c_user, channel_users)

                    # Send a room update packet to the lobby if there are players left
                    if c_user.room_page == this_room_page and not is_last_player:
                        room_update = PacketFactory.create_packet(
                            packet_id=PacketList.DO_ROOM_INFO_CHANGE,
                            room_to_update=room_left,
                            update_type=gconstants.RoomUpdateType.UPDATE,
                            viewer=c_user,
                        )
                        await c_user.send(room_update.build())


class RoomListHandler(PacketHandler):
    """DO_ROOM_LIST request: <target> <waiting only> <backward> (client builder PF20 0x469114,
    PF23 0x469590).

    - All rooms (block 1 = 0, the default): block 0 is the page the client wants. Next / previous
      send page+1 / page-1, the SHOW ALL / SHOW AVAIL toggle and /go send page 0 or the page of a room.
    - Waiting only (block 1 = 1): block 0 is a room id. Next sends the highest id on screen + 1,
      previous the lowest id on screen, with block 2 = 1.
    """

    async def process(self, user: "User"):
        if not user.authorized:
            return

        if user.room is not None:
            return

        target = int(self.get_block(0))
        user.room_list_waiting = int(self.get_block(1)) == 1
        backward = int(self.get_block(2)) == 1

        channel = user.this_server.channels[user.channel]

        if not user.room_list_waiting:
            user.room_page = max(0, target)
        else:
            rooms = (await channel.get_all_rooms()).values()
            waiting_ids = sorted(room.id for room in rooms if room.state == gconstants.RoomStatus.WAITING)

            if backward:
                # The 8 waiting rooms right before the first one on screen
                before = [room_id for room_id in waiting_ids if room_id < target][-8:]
                anchor = before[0] if before else 0
            else:
                after = [room_id for room_id in waiting_ids if room_id >= target]
                # Nothing further on (or the toggle with no waiting rooms): keep the current list
                anchor = after[0] if after else user.room_list_anchor

            user.room_list_anchor = anchor

        await channel.send_room_list(user)


class RoomInviteHandler(PacketHandler):
    async def process(self, user: "User"):

        if not user.authorized:
            return

        if user.room is None or user.room.state == gconstants.RoomStatus.PLAYING:
            return

        # Check if the room is full
        if len(user.room.get_all_players()) >= user.room.max_players:
            # TODO: Handle the "room is full" error
            return

        user_to_invite = self.get_block(0)
        message = self.get_block(1)

        # Get the channel of the player who's inviting
        this_channel = user.this_server.channels[user.channel]

        player_pool = [
            cuser for cuser in await this_channel.get_users() if cuser.room is None
        ]

        if user_to_invite == "NULL":
            # Randomly invite a user from the pool
            if not player_pool:
                await self.send_error(user, RoomInvitationError.GENERIC)
            else:
                target_user = random.choice(player_pool)
                await self.send_invitation(user, target_user, message)
        else:
            # Invite a specific user by displayname
            target_user = next(
                (
                    u
                    for u in await this_channel.get_users()
                    if u.displayname == user_to_invite
                ),
                None
            )

            if target_user and target_user.room is None:
                await self.send_invitation(user, target_user, message)
            else:
                error_code = (
                    RoomInvitationError.ALREADY_IN_ROOM
                    if target_user and target_user.room is not None
                    else RoomInvitationError.GENERIC
                )
                await self.send_error(user, error_code)

    async def send_invitation(self, inviter: "User", invitee: "User", message: str):
        invite_packet = PacketFactory.create_packet(
            packet_id=PacketList.DO_INVITATION,
            error_code=1,
            user=inviter,
            message=message,
        )
        # For the "invitation has been sent" msg, you have to resend the packet again. Yup
        await inviter.send(invite_packet.build())
        await invitee.send(invite_packet.build())

    async def send_error(self, user: "User", error_code):
        error_packet = PacketFactory.create_packet(
            packet_id=PacketList.DO_INVITATION, error_code=error_code
        )
        await user.send(error_packet.build())


class RoomExpelHandler(PacketHandler):
    async def process(self, user: "User"):

        if not user.authorized:
            return

        if user.room is None:
            return

        this_room = user.room

        if this_room.master != user:
            return

        slot_to_kick = int(self.get_block(0))

        target_player = this_room.players.get(slot_to_kick)

        if target_player is None or slot_to_kick == this_room.master_slot:
            return
        else:
            kick_packet = PacketFactory.create_packet(
                packet_id=PacketList.DO_EXPEL_PLAYER,
                target_player=slot_to_kick
            )

            await target_player.user.send(kick_packet.build())


class RoomSpectateHandler(PacketHandler):
    async def process(self, user: "User"):

        if not user.authorized or user.rights < 3:
            return

        # leave = 0 / join = 1
        join_or_leave = int(self.get_block(0))

        if join_or_leave == gconstants.RoomSpectateAction.JOIN:
            room_id = int(self.get_block(1))

            this_room = user.this_server.channels[user.channel].rooms[room_id]

            # TODO: any error code we can use?
            if not this_room:
                return

            spec_id = await this_room.add_spectator(user)
            print(f"Assigned spec id {spec_id}")

        elif join_or_leave == gconstants.RoomSpectateAction.LEAVE:
            pass
        else:
            return
