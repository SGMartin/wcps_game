from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_core.constants import ErrorCodes as corerr

import wcps_game.game.constants as gconstants

from wcps_game.game.rooms import Room
from wcps_game.handlers.packet_handler import PacketHandler
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.error_codes import RoomCreateError


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
        default_longest_name = "Let\'s\x1dplay\x1dWarRock\x1dtoday!!!"

        if len(room_name) not in range(0, 26) and room_name != default_longest_name:
            await self.send_generic_error(user)
            return

        # Validate password
        if has_password and (len(input_password) not in range(1, 11) or input_password == "NULL"):
            await self.send_generic_error(user)
            return

        # Validate max players
        # 8/16/20/24/32 in CP 1 :)
        # 0/1/2/3/4

        max_players_for_room = len(gconstants.RoomMaximumPlayers.MAXIMUM_PLAYERS[user.channel])

        if player_limit > max_players_for_room:
            await self.send_generic_error(user)
            return

        # Validate minimum level requirements
        this_player_level = gconstants.get_level_for_exp(user.xp)
        requested_limit = gconstants.RoomLevelLimits.MIN_LEVEL_REQUIREMENTS.get(level_limit)

        if requested_limit is None or this_player_level not in requested_limit:
            level_error = PacketFactory.create_packet(
                packet_id=PacketList.ROOM_CREATE,
                error_code=RoomCreateError.UNSUITABLE_LEVEL
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
            is_clanwar=False  # TODO: investigate it in the future
        )

        this_channel = user.this_server.channels[user.channel]
        new_room_id = await this_channel.add_room(new_room)

        if new_room_id is None:
            too_many_rooms = PacketFactory.create_packet(
                packet_id=PacketList.ROOM_CREATE,
                error_code=RoomCreateError.MAX_ROOM_LIMIT
            )
            await user.send(too_many_rooms.build())
            return

        new_room.authorize(room_id=new_room_id)

        room_create_packet = PacketFactory.create_packet(
            packet_id=PacketList.ROOM_CREATE,
            error_code=corerr.SUCCESS,
            new_room=new_room
        )

        # The master user has been notified
        await user.send(room_create_packet.build())

        # Notify the rest of the lobby
        # TODO: investigate room pages
        # await this_channel.broadcast_packet_to_channel(room_create_packet.build())

    async def send_generic_error(user: "User"):
        error_packet = PacketFactory.create_packet(
            packet_id=PacketList.ROOM_CREATE,
            error_code=RoomCreateError.GENERIC
        )
        await user.send(error_packet.build())


class RoomLeaveHandler(PacketHandler):
    async def process(self, user: "User"):

        if not user.authorized:
            return

        if user.room is not None:
            await user.room.remove_player(user)

        print("IMPLEMENT LOBBY UPDATE HERE")
