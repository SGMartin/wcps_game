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


class RoomCreateHandler(PacketHandler):
    async def process(self, user: "User"):
        # bytearray(b'50910153 29440 Mediavida 1 hello 1 12 0 0 0 3 1 1 \n')

        if not user.authorized:
            return

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

        if player_limit > max_players_for_room:
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
            if user_to_update.room is None and user.room_page == new_room.room_page:
                update_packet = PacketFactory.create_packet(
                    packet_id=PacketList.DO_ROOM_INFO_CHANGE,
                    room_to_update=new_room,
                    update_type=gconstants.RoomUpdateType.CREATE,
                )
                await user_to_update.send(update_packet.build())

    async def send_generic_error(user: "User"):
        error_packet = PacketFactory.create_packet(
            packet_id=PacketList.ROOM_CREATE, error_code=RoomCreateError.GENERIC
        )
        await user.send(error_packet.build())


class RoomJoinHandler(PacketHandler):
    async def process(self, user: "User"):
        if not user.authorized:
            return

        if user.room is not None:
            return

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

        if this_room.premium_only and user.premium == gconstants.Premium.F2P:
            not_premium = PacketFactory.create_packet(
                packet_id=PacketList.DO_JOIN_ROOM,
                error_code=RoomJoinError.PREMIUM_ONLY,
                room_to_join=None,
            )
            await user.send(not_premium.build())
            return

        # Player level is unsuitable
        this_player_level = gconstants.get_level_for_exp(user.xp)
        level_required = gconstants.RoomLevelLimits.MIN_LEVEL_REQUIREMENTS.get(
            this_room.level_limit
        )

        if this_player_level not in level_required:
            bad_level_error = PacketFactory.create_packet(
                packet_id=PacketList.DO_JOIN_ROOM,
                error_code=RoomJoinError.UNSUITABLE_LEVEL,
                room_to_join=None
            )
            await user.send(bad_level_error.build())
            return

        if user.username in this_room.votekick.locked_users:
            voted_out_error = PacketFactory.create_packet(
                packet_id=PacketList.DO_JOIN_ROOM,
                error_code=RoomJoinError.GENERIC,
                room_to_join=None
            )
            await user.send(voted_out_error.build())
            return

        # If this function does not return none, it will send the room join packet
        player = await this_room.add_player(user)

        if player is None:
            if this_room.user_limit:
                cannot_join_error = PacketFactory.create_packet(
                    packet_id=PacketList.DO_JOIN_ROOM,
                    error_code=RoomJoinError.MAX_USERS,
                    room_to_join=None,
                )
                await user.send(cannot_join_error.build())
            else:
                room_full_error = PacketFactory.create_packet(
                    packet_id=PacketList.DO_JOIN_ROOM,
                    error_code=RoomJoinError.ROOM_FULL,
                    room_to_join=None,
                )
                await user.send(room_full_error.build())
        else:
            return


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
            user_list_full = PacketFactory.create_packet(
                packet_id=PacketList.USERLIST,
                lobby_user_list=channel_users,
                target_page=user.userlist_page,
            )
            await user.send(user_list_full.build())

            # Send the user the room list
            all_rooms = await user.this_server.channels[user.channel].get_all_rooms()
            rooms_to_send = [
                room for room in all_rooms.values() if room.room_page == user.room_page
            ]

            new_room_list = PacketFactory.create_packet(
                packet_id=PacketList.DO_ROOM_LIST,
                room_page=user.room_page,
                room_list=rooms_to_send,
            )
            await user.send(new_room_list.build())

            # Send an userlist packet for all users in the user list for their current page
            # TODO: check if packet DO_USERLIST_CHANGE (0x7110) would work here?
            # TODO: IS this really necessary? He has not left the channel...
            for c_user in channel_users:
                if c_user.room is None:
                    this_user_update = PacketFactory.create_packet(
                        packet_id=PacketList.USERLIST,
                        lobby_user_list=channel_users,
                        target_page=c_user.userlist_page,
                    )
                    await c_user.send(this_user_update.build())

                    # Send a room update packet to the lobby if there are players left
                    if c_user.room_page == this_room_page and not is_last_player:
                        room_update = PacketFactory.create_packet(
                            packet_id=PacketList.DO_ROOM_INFO_CHANGE,
                            room_to_update=room_left,
                            update_type=gconstants.RoomUpdateType.UPDATE,
                        )
                        await c_user.send(room_update.build())


class RoomListHandler(PacketHandler):
    async def process(self, user: "User"):
        if not user.authorized:
            return

        if user.room is not None:
            return
        # 2024-08-11 00:06:22,839 - INFO - IN:: bytearray(b'27754355 29184 1 0 0 \n')
        # go_forward = bool(int(self.get_block(0)))
        show_waiting = False if int(self.get_block(1)) == 1 else True
        go_backward = bool(int(self.get_block(2)))

        if go_backward:
            user.room_page = user.room_page - 1
        else:
            user.room_page = user.room_page + 1

        if user.room_page < 0:
            user.room_page = 0

        all_channel_rooms = await user.this_server.channels[
            user.channel
        ].get_all_rooms()
        last_waiting_rooms = []
        last_rooms = []

        for idx, room in all_channel_rooms.items():
            if room is not None:
                if room.id >= 8 * user.room_page and room.id < 8 * (user.room_page + 1):
                    last_rooms.append(room)
                if room.state == gconstants.RoomStatus.WAITING:
                    last_waiting_rooms.append(room)

        if show_waiting:
            rooms_to_send = last_waiting_rooms[-8:]
        else:
            rooms_to_send = last_rooms

        room_packet = PacketFactory.create_packet(
            packet_id=PacketList.DO_ROOM_LIST,
            room_page=user.room_page,
            room_list=rooms_to_send,
        )
        # TODO: recheck filtering step of waiting rooms
        await user.send(room_packet.build())


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
