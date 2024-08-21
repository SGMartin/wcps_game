import asyncio
import logging
import math

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User
    from wcps_core.packets import OutPacket

from wcps_core.constants import ErrorCodes as corerr

from wcps_game.game import constants as gconstants
from wcps_game.game.player import Player
from wcps_game.game.ground_item import GroundItem

from wcps_game.game.game_modes.ffa import FFA

from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory


class Room:
    def __init__(
        self,
        master: "User",
        displayname: str,
        password_protected: bool,
        password: str = "",
        max_players: int = 0,
        room_type: int = 0,
        level_limit: int = 0,
        premium_only: bool = False,
        vote_kick: bool = True,
        is_clanwar: bool = False,
    ):

        # Defined at room creation
        self.id = -1
        self.room_page = None
        self.displayname = displayname

        self.channel = master.this_server.channels[master.channel]
        self.type = room_type  # Unused in CP1
        self.level_limit = level_limit
        self.premium_only = premium_only
        self.vote_kick = vote_kick
        self.is_clanwar = is_clanwar

        self.password_protected = password_protected

        if password_protected:
            self.password = password
        else:
            self.password = None

        if master.inventory.has_item("CC02"):
            self.supermaster = True
        else:
            self.supermaster = False

        self.max_players = gconstants.RoomMaximumPlayers.MAXIMUM_PLAYERS[
            self.channel.type
        ][max_players]

        self.running = False

        # Auto/default settings on room creating
        self.state = gconstants.RoomStatus.WAITING
        self.rounds_setting = 3  # Packet specific
        self.tickets_setting = 3  # Packet specific
        self.rounds = gconstants.ROUND_LIMITS[self.rounds_setting]  # Actual setting
        self.tdm_tickets = gconstants.TDM_LIMITS[self.tickets_setting]  # Actual setting
        self.autostart = False
        self.user_limit = False
        self.ground_items = {}

        # Set a default map for each mode
        map_defaults = {
            gconstants.ChannelType.CQC: 12,  # Marien
            gconstants.ChannelType.URBANOPS: 0,  # Montana
            gconstants.ChannelType.BATTLEGROUP: 2,  # Emblem
        }

        self.current_map = map_defaults[self.channel.type]

        default_modes = {
            gconstants.ChannelType.CQC: gconstants.GameMode.EXPLOSIVE,
            gconstants.ChannelType.URBANOPS: gconstants.GameMode.TDM,
            gconstants.ChannelType.BATTLEGROUP: gconstants.GameMode.TDM,
        }

        self.game_mode = default_modes[self.channel.type]
        self.current_game_mode = None  # This will hold a reference for the actual game mode
        self.ping_limit = gconstants.RoomPingLimit.GREEN

        # Set the user who sent the packet as the default master
        self.master = master
        self.master_slot = 0
        self.master.set_room(self, room_slot=0)

        # Add the master as a player to the dict of players
        this_player = Player(
            user=self.master, slot=self.master_slot, team=gconstants.Team.DERBARAN
        )
        this_player.ready = True

        # User data for networking
        self.players = dict.fromkeys(range(0, self.max_players))
        self.players[0] = this_player

        self._players_lock = asyncio.Lock()
        self._items_lock = asyncio.Lock()

    def authorize(self, room_id: int):
        self.id = room_id
        self.room_page = round(math.floor(self.id / 8))

    def update_rounds_from_settings(self, settings: int):
        self.rounds = gconstants.ROUND_LIMITS[settings]
        self.rounds_setting = settings

    def update_tickets_from_settings(self, settings: int):
        self.tdm_tickets = gconstants.TDM_LIMITS[settings]
        self.tickets_setting = settings

    def get_player_count_in_team(self, team_to_count) -> int:
        player_count = 0

        if team_to_count == gconstants.Team.DERBARAN:
            slot_range = range(0, math.floor(self.max_players / 2))
        else:
            slot_range = range(math.floor(self.max_players / 2), self.max_players)

        for slot in slot_range:
            if self.players[slot] is not None:
                player_count += 1

        return player_count

    def get_ready_player_count_in_team(self, team_to_count) -> int:
        player_count = 0

        if team_to_count == gconstants.Team.DERBARAN:
            slot_range = range(0, math.floor(self.max_players / 2))
        else:
            slot_range = range(math.floor(self.max_players / 2), self.max_players)

        for slot in slot_range:
            if self.players[slot] is not None:
                if self.players[slot].ready:
                    player_count += 1

        return player_count

    def get_player_count(self) -> int:
        player_count = 0
        for player in self.players.values():
            if player is not None:
                player_count += 1
        return player_count

    def get_all_players(self) -> list:
        return [player for player in self.players.values() if player is not None]

    def get_player_team(self, player_slot: int) -> int:
        return self.players[player_slot].team

    async def add_player(self, user: "User") -> Player:

        this_player = None

        if self.get_player_count() >= self.max_players or self.user_limit:
            return this_player

        async with self._players_lock:
            player_team = gconstants.Team.DERBARAN

            current_derbaran_players = self.get_player_count_in_team(
                gconstants.Team.DERBARAN
            )
            current_niu_players = self.get_player_count_in_team(gconstants.Team.NIU)

            if current_derbaran_players > current_niu_players:
                player_team = gconstants.Team.NIU

            # Ok, to find the team, remember that the first half of the slots are always derbaran
            # and the second half, NIU
            if player_team == gconstants.Team.DERBARAN:
                slot_range = range(0, math.floor(self.max_players / 2))
            else:
                slot_range = range(math.floor(self.max_players / 2), self.max_players)

            for requested_slot in slot_range:
                if self.players[requested_slot] is None:
                    this_player = Player(
                        user=user, slot=requested_slot, team=player_team
                    )

                    # Send the incoming user the room join packet
                    join_packet = PacketFactory.create_packet(
                        packet_id=PacketList.DO_JOIN_ROOM,
                        error_code=corerr.SUCCESS,
                        room_to_join=self,
                        player_slot=requested_slot,
                    )

                    user.set_room(room=self, room_slot=requested_slot)
                    await user.send(join_packet.build())

                    # Now add the player to the list of players
                    self.players[requested_slot] = this_player

                    room_players_packet = PacketFactory.create_packet(
                        packet_id=PacketList.DO_GAME_USER_LIST,
                        player_list=self.get_all_players()
                    )
                    await self.send(room_players_packet.build())

                    # Send an update to the lobby
                    channel_users = await self.channel.get_users()

                    for user in channel_users:
                        if user.room is None and user.room_page == self.room_page:
                            room_update = PacketFactory.create_packet(
                                packet_id=PacketList.DO_ROOM_INFO_CHANGE,
                                room_to_update=self,
                                update_type=gconstants.RoomUpdateType.UPDATE,
                            )
                            await user.send(room_update.build())
                    break

        return this_player

    async def switch_player_side(self, player_to_switch: Player):

        can_switch = False

        max_team_size = round(self.max_players / 2)
        target_team = (
            gconstants.Team.DERBARAN
            if player_to_switch.team == gconstants.Team.NIU
            else gconstants.Team.NIU
        )
        target_team_players = self.get_player_count_in_team(target_team)

        if target_team_players >= max_team_size or self.is_clanwar:
            return

        if target_team == gconstants.Team.DERBARAN:
            slot_range = range(0, math.floor(self.max_players / 2))
        else:
            slot_range = range(math.floor(self.max_players / 2), self.max_players)

        async with self._players_lock:

            for requested_slot in slot_range:
                if self.players[requested_slot] is None:

                    # Get the old player slot
                    old_slot = player_to_switch.id

                    # Update the player object stats
                    player_to_switch.team = target_team
                    player_to_switch.id = requested_slot
                    player_to_switch.user.room_slot = requested_slot

                    # Insert it into the slot
                    self.players[requested_slot] = player_to_switch

                    # Remove it from the old slot
                    self.players[old_slot] = None

                    if old_slot == self.master_slot:
                        self.master = player_to_switch.user
                        self.master_slot = requested_slot

                    can_switch = True
                    break

                can_switch = False

        return can_switch

    async def remove_player(self, user: "User"):
        if not user.authorized or user.room is None:
            return

        if (
            self.id != user.room.id
        ):  # Is the user somehow removing himself from other room?
            return

        async with self._players_lock:
            if self.players.get(user.room_slot) is None:
                return

            old_player = self.players[user.room_slot]

            # Release the slot and set the player room slot to 0
            self.players[user.room_slot] = None
            # Set the room to none and ask to update k/d as vanilla warrock did
            user.set_room(None, 0)
            # TODO: should we call this ONLY if there were changes to the player stats?
            await user.update_stats()

            if self.get_player_count() == 0:  # Empty room, destroy it
                await self.destroy()
            else:
                if old_player.id == self.master_slot:  # This player was the master

                    # This is not a supermaster room anymore
                    # TODO: What the original server did if the new master was also SP?
                    if self.supermaster:
                        self.supermaster = False

                    # Calculate the priority level for the new master
                    all_players = self.get_all_players()
                    new_master = None
                    best_priority = 0

                    for player in all_players:
                        player_priority = player.user.premium + 1

                        if player.user.inventory.has_item("CC02"):
                            player_priority += 1

                        if player_priority > best_priority:
                            new_master = player
                            best_priority = player_priority

                    if new_master is not None:
                        self.master = new_master.user
                        self.master_slot = new_master.id
                        self.players[self.master_slot].ready = True
                    else:
                        await self.destroy()
                        logging.error(f"Could not find a new master for room {self.id}")

            # Finally, send the room leave packet
            room_leave = PacketFactory.create_packet(
                packet_id=PacketList.DO_EXIT_ROOM,
                user=user,
                room=self,
                old_slot=old_player.id,
            )
            # Send it to the user
            await user.send(room_leave.build())
            # Send it to the rest of the room
            await self.send(room_leave.build())

    async def add_item(self, owner: Player, code: str):
        async with self._items_lock:
            new_item = GroundItem(owner=owner, code=code)
            new_item.place(room_id=len(self.ground_items) + 1)
            self.ground_items[new_item.id] = new_item

    async def destroy(self):
        # Get the users in the channel
        channel_users = await self.channel.get_users()
        # Clear the room slot from the channel
        await self.channel.remove_room(self.id)
        # Clear players of the room
        for room_player in self.get_all_players():
            room_player.user.set_room(None, 0)

        for user in channel_users:
            if user.room is None and user.room_page == self.room_page:
                # TODO: is this packet necessary?
                room_delete = PacketFactory.create_packet(
                    packet_id=PacketList.DO_ROOM_INFO_CHANGE,
                    room_to_update=self,
                    update_type=gconstants.RoomUpdateType.DELETE,
                )
                await user.send(room_delete.build())

                # send them also the room list
                room_list_for_page = await user.this_server.channels[
                    user.channel
                ].get_all_rooms()
                room_list_for_page = [
                    room
                    for room in room_list_for_page.values()
                    if room.room_page == user.room_page
                ]

                new_room_list = PacketFactory.create_packet(
                    packet_id=PacketList.DO_ROOM_LIST,
                    room_page=user.room_page,
                    room_list=room_list_for_page,
                )
                await user.send(new_room_list.build())

    async def send(self, buffer: "OutPacket"):
        for player in self.players.values():
            if player is not None:
                await player.user.send(buffer)

    async def start(self):
        self.up_ticks = 0
        self.down_ticks = 1800000
        self.last_tick = -1

        for player in self.get_all_players():
            player.reset_game_state()
            player.round_start()

        # Initialize the game modes
        game_modes = {
            gconstants.GameMode.FFA: FFA,
            gconstants.GameMode.TDM: FFA  # test distances
        }

        self.ground_items = {}  # Empty the ground items dictionary
        self.current_game_mode = game_modes[self.game_mode]()
        self.current_game_mode.initialize(self)
        logging.info(f"Room {self.id} started")

    async def end_game(self, winner_team: gconstants.Team):
        logging.info(f"Current game state is {self.state}")
        if self.state != gconstants.RoomStatus.PLAYING:
            return

        players = self.get_all_players()

        # TODO: send the statistics here
        for player in players:
            await player.end_game()

        end_game_packet = PacketFactory.create_packet(
            packet_id=PacketList.DO_GAME_RESULT,
            room=self,
            players=self.get_all_players(),
            winner_team=winner_team
        )
        await self.send(end_game_packet.build())

        self.current_game_mode = None
        self.state = gconstants.RoomStatus.WAITING
        self.running = False

        # Send a new room update packet so that k/d stats are updated
        room_players = PacketFactory.create_packet(
            packet_id=PacketList.DO_GAME_USER_LIST,
            player_list=self.get_all_players()
        )
        await self.send(room_players.build())

        logging.info(f"Room {self.id} ended")

    async def run(self):
        try:
            last_tick_time = datetime.now()

            while self.state == gconstants.RoomStatus.PLAYING:
                if self.current_game_mode is not None and self.current_game_mode.initialized:

                    if self.current_game_mode.is_goal_reached():  # Game ended
                        await self.end_game(self.current_game_mode.winner())
                        break  # TODO: check if we should actually do this

                    if self.current_game_mode.freeze_tick:
                        self.last_tick = -1
                    else:
                        # Call the game mode routine here
                        await self.current_game_mode.process()

                        current_time = datetime.now()
                        elapsed_time = (current_time - last_tick_time).total_seconds()

                        if elapsed_time >= 1:
                            self.up_ticks += 1000
                            self.down_ticks -= 1000
                            self.last_tick = current_time.second

                            # Create and send clock packet
                            clock_packet = PacketFactory.create_packet(
                                packet_id=PacketList.DO_GAME_UPDATE_CLOCK, room=self
                            )
                            await self.send(clock_packet.build())
                            await self.update_spawn_protection()

                            # Reset the last_tick_time
                            last_tick_time = current_time

                # Sleep for a short interval to allow for precise timing
                await asyncio.sleep(0.01)

        except Exception as e:
            logging.error(f"Error in core room loop {e}", exc_info=True)

    async def update_spawn_protection(self):
        room_players = self.get_all_players()

        for player in room_players:
            if player.alive and player.spawn_protection_ticks > 0:
                player.spawn_protection_ticks -= 1000

            if player.spawn_protection_ticks < 0:
                player.spawn_protection_ticks = 0
