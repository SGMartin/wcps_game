import asyncio
import logging
import math
import time

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User
    from wcps_core.packets import OutPacket

from wcps_core.constants import ErrorCodes as corerr

from wcps_game.client.maps import MapDatabase
from wcps_game.client.vehicle_catalogue import VehicleCatalogue
from wcps_game.game import constants as gconstants
from wcps_game.game.player import Player
from wcps_game.game.ground_item import GroundItem

from wcps_game.game.game_modes.ffa import FFA
from wcps_game.game.game_modes.tdm import TDM
from wcps_game.game.game_modes.explosives import Explosive
from wcps_game.game.game_modes.conquest import Conquest

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

        # TODO: make this configurable
        self.max_spectators = 4

        self.running = False

        # Auto/default settings on room creating
        self.state = gconstants.RoomStatus.WAITING
        self.rounds_setting = 3  # Packet specific
        self.tickets_setting = 3  # Packet specific
        self.rounds = gconstants.ROUND_LIMITS[self.rounds_setting]  # Actual setting
        self.tdm_tickets = gconstants.TDM_LIMITS[self.tickets_setting]  # Actual setting
        self.autostart = False
        self.user_limit = False
        self.enable_votekick = vote_kick  # vote kick setting as defined in room creating
        self.votekick = VoteKick(self)  # always instanciate a new votekick object just in case
        self.ground_items = {}
        self.flags = {}
        self.spawn_flags = {}
        self.vehicles = {}

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
        self.spectators = dict.fromkeys(range(32, 32 + self.max_spectators))
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
                    # Get the current player list
                    current_players = self.get_all_players()

                    # First, notify the users of the new player
                    new_player_data = PacketFactory.create_packet(
                        packet_id=PacketList.DO_GAME_USER_LIST,
                        player_list=[this_player]
                    )
                    await self.send(new_player_data.build())

                    # Send the incoming user the room join packet
                    join_packet = PacketFactory.create_packet(
                        packet_id=PacketList.DO_JOIN_ROOM,
                        error_code=corerr.SUCCESS,
                        room_to_join=self,
                        player_slot=requested_slot,
                    )

                    user.set_room(room=self, room_slot=requested_slot)
                    await user.send(join_packet.build())

                    # Important: these packets must be sent in this order
                    # For UDP to work for all of them and not for some user

                    room_players_packet = PacketFactory.create_packet(
                        packet_id=PacketList.DO_GAME_USER_LIST,
                        player_list=current_players
                    )
                    await self.send(room_players_packet.build())

                    # Now add the player to the list of players
                    self.players[requested_slot] = this_player

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

    # TODO: complete this
    async def add_spectator(self, spectator: "User"):
        current_specs = [spec for spec in self.spectators.values() if spec]
        if len(current_specs) >= self.max_spectators:
            return None
        else:
            slot_to_test = 16
            self.spectators[slot_to_test] = spectator
            spectator.set_room(room=self, room_slot=slot_to_test)

            # Spectate packet to join the room
            spectate_packet = PacketFactory.create_packet(
                packet_id=PacketList.DO_GUEST_JOIN,
                room_to_join=self,
                spectate_slot=slot_to_test
            )
            await spectator.send(spectate_packet.build())
            # Players information and UPP endpoint
            room_players_packet = PacketFactory.create_packet(
                        packet_id=PacketList.DO_GAME_USER_LIST,
                        player_list=self.get_all_players()
                    )

            await spectator.send(room_players_packet.build())

            # Send players the spectator list?
            specs_list = PacketFactory.create_packet(
                packet_id=PacketList.DO_GAME_GUEST_LIST,
                spec=spectator,
                slot=slot_to_test
            )
            # await self.send(specs_list.build())
            for player in self.get_all_players():
                if player is not None:
                    await player.user.send(specs_list.build())
            return slot_to_test

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

            # Are we playing and is he in a vehicle?
            if old_player.vehicle_id != -1:
                this_vehicle = self.vehicles.get(old_player.vehicle_id)

                if this_vehicle is not None:
                    result = await this_vehicle.leave_vehicle(old_player)

                    if not result:
                        logging.error(f"Could not leave {this_vehicle.id} for {old_player.id}")

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
            # WarRock CP1 glitches if the first id is 0. It won't even send activate packets
            # Until the client is restarted
            new_id = len(self.ground_items) + 1
            await new_item.place(room_id=new_id)
            self.ground_items[new_item.id] = new_item

            return new_id

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

        for spectator in self.spectators.values():
            if spectator is not None:
                await spectator.send(buffer)

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
            gconstants.GameMode.TDM: TDM,
            gconstants.GameMode.EXPLOSIVE: Explosive,
            gconstants.GameMode.CONQUEST: Conquest
        }

        self.ground_items = {}  # Empty the ground items dictionary

        # Populate the flags dictionaries
        map_database = MapDatabase()
        this_map_flags = map_database.get_flag_number(map_id=self.current_map)
        default_team_flags = map_database.get_spawn_flags(map_id=self.current_map)

        self.flags = dict.fromkeys(range(0, this_map_flags), -1)
        self.spawn_flags = default_team_flags

        # By default, set the derbaran spawn flag as team derbaran and the niu spawn flag as niu
        # Remember that in conquest we flush spawn flags so this better be ready
        self.flags[self.spawn_flags[gconstants.Team.DERBARAN]] = gconstants.Team.DERBARAN
        self.flags[self.spawn_flags[gconstants.Team.NIU]] = gconstants.Team.NIU

        # Populate the vehicle dictionary if needed
        vehicle_catalogue = VehicleCatalogue()
        self.vehicles = vehicle_catalogue.get_vehicles_for_map(map_id=self.current_map)

        # Initialize game mode
        self.current_game_mode = game_modes[self.game_mode]()
        await self.current_game_mode.initialize(self)

        logging.info(f"Room {self.id} started")

    async def end_game(self, winner_team: gconstants.Team):
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

        # Flush flag status
        self.flags.clear()
        self.spawn_flags.clear()
        # Empty game items
        self.ground_items.clear()
        # Empty all of the vehicle references
        self.vehicles.clear()
        # Reset game mode
        self.current_game_mode = None
        self.state = gconstants.RoomStatus.WAITING
        self.running = False
        # Reset kicked users set
        self.votekick.locked_users.clear()

        # Send a new room update packet so that k/d stats are updated
        # Commented out. We need tests to ensure sending the full packet does not
        # end with UDP breaking
        # room_players = PacketFactory.create_packet(
        #     packet_id=PacketList.DO_GAME_USER_LIST,
        #     player_list=self.get_all_players()
        # )
        # await self.send(room_players.build())

        logging.info(f"Room {self.id} ended")

    async def run(self):
        try:
            last_tick_time = datetime.now()
            map_update_timer = 0

            while self.state == gconstants.RoomStatus.PLAYING:
                if self.current_game_mode is not None and self.current_game_mode.initialized:

                    if self.current_game_mode.is_goal_reached():  # Game ended
                        await self.end_game(self.current_game_mode.winner())
                        break  # TODO: check if we should actually do this

                    # If not goal reached, call process routine
                    await self.current_game_mode.process()

                    # Check again the game mode did not end after process call
                    if self.current_game_mode and self.current_game_mode.freeze_tick:
                        self.last_tick = -1
                    else:
                        current_time = datetime.now()
                        elapsed_time = (current_time - last_tick_time).total_seconds()

                        if elapsed_time >= 1:
                            self.up_ticks += 1000
                            self.down_ticks -= 1000
                            self.last_tick = current_time.second
                            map_update_timer += 1

                            # Create and send clock packet
                            clock_packet = PacketFactory.create_packet(
                                packet_id=PacketList.DO_GAME_UPDATE_CLOCK, room=self
                            )
                            await self.send(clock_packet.build())
                            await self.update_spawn_protection()
                            await self.update_vehicle_spawn()
                            await self.update_vehicle_unused_time()
                            await self.handle_votekick()
                            await self.handle_bleeding()

                            # TODO: is 5 seconds ok?
                            if map_update_timer >= 5:
                                map_update = PacketFactory.create_packet(
                                    packet_id=PacketList.DO_GAME_UPDATE_DATA,
                                    room=self
                                )
                                await self.send(map_update.build())
                                map_update_timer = 0

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

    async def update_vehicle_spawn(self):
        if len(self.vehicles) == 0:
            return
        for vehicle in self.vehicles.values():
            if vehicle.health > 0:
                continue

            # TODO: spawned vehicles should be protected by spawn protection?
            if vehicle.broken_time >= vehicle.spawn_time:
                await vehicle.reset()
                spawn_packet = PacketFactory.create_packet(
                    packet_id=PacketList.DO_UNIT_REGEN,
                    room=self,
                    target_vehicle=vehicle
                )
                await self.send(spawn_packet.build())
            else:
                vehicle.broken_time += 1000

    async def update_vehicle_unused_time(self):
        if len(self.vehicles) == 0:
            return

        for vehicle in self.vehicles.values():
            if vehicle.health <= 0 or vehicle.team != gconstants.Team.NONE:
                continue

            if vehicle.update_string == "":  # Vehicle spawned but never used
                continue

            if vehicle.unused_time <= 600000:  # 10 minutes afk time. TODO: configure this
                vehicle.unused_time += 1000
            else:
                vehicle.health = 0
                vehicle_explosion = PacketFactory.create_packet(
                    packet_id=PacketList.DO_UNIT_DIE,
                    room=self,
                    target_vehicle=vehicle
                )
                await self.send(vehicle_explosion.build())

    async def handle_votekick(self):
        if not self.votekick.running:
            return

        votes_to_kick = len(self.votekick.get_positive_votes())
        # votes_to_save = len(self.votekick.get_negative_votes())

        players_in_team = self.get_player_count_in_team(
            team_to_count=self.votekick.vote_team
        )
        majority = round(players_in_team / 2) + 1
        should_kick = votes_to_kick >= majority

        if time.time() >= self.votekick.timestamp:
            await self.votekick.stop_vote(should_kick)
        elif should_kick:
            await self.votekick.stop_vote(kicked=True)

    async def handle_bleeding(self):
        # No bleeding out in cqc
        if self.channel.type == gconstants.ChannelType.CQC:
            return

        for player in self.get_all_players():
            # Bleeding out threshold is 3 hp
            if not player.alive or player.health > 300:
                continue

            # Compressed bandage
            if player.user.inventory.has_item("CH01"):
                continue

            # TODO: make this timer configurable and research original settings
            if player.bleeding_timer < 10:
                player.bleeding_timer += 1
            else:
                player.bleeding_timer = 0
                # TODO: also make this configurable
                player.health = player.health - 50

                if player.health <= 0:
                    suicide_packet = PacketFactory.create_packet(
                        packet_id=PacketList.DO_SUICIDE,
                        room=self,
                        player=player,
                        suicide_type=1,  # TODO: make enum
                        out_of_map_limits=False
                    )
                    await player.add_deaths()
                    await self.current_game_mode.on_suicide(player=player)
                    await self.send(suicide_packet.build())


class VoteKick:
    def __init__(self, room):
        self.room = room
        self.votes = []
        self.vote_side = -1
        self.target_id = -1
        self.running = False
        self.timestamp = 0
        self.last_kick_timestamp = 0
        self.locked_users = set()  # Set of users who have been kicked/locked out

    def start_vote(self, target_slot, side):
        self.running = True
        self.target_id = target_slot
        self.vote_team = side
        self.timestamp = self.get_timestamp() + 30

    async def stop_vote(self, kicked):
        # kick the user if needed
        await self.kick_user(kicked)

        self.running = False
        self.timestamp = 0
        self.target_id = -1
        self.vote_team = -1

        self.last_kick_timestamp = self.get_timestamp()
        self.votes.clear()  # Clear the list of votes

    def add_user_vote(self, user, kick):
        # I think only positive votes return a packet, but keep a dict nevertheless just in case
        vote = {"user": user, "kick": kick}
        self.votes.append(vote)

    def get_positive_votes(self):
        return [vote for vote in self.votes if vote["kick"]]

    def get_negative_votes(self):
        return [vote for vote in self.votes if not vote["kick"]]

    async def kick_user(self, kicked):

        player = self.room.players.get(self.target_id)

        if kicked and player:
            # Send a kick packet, which in turn will trigger a normal room leave packet
            # and handler. No need to send lobby updates to the player
            kick_packet = PacketFactory.create_packet(
                packet_id=PacketList.DO_EXPEL_PLAYER,
                target_player=player.id
            )
            await player.user.send(kick_packet.build())

            # add the player to the list of kicked players
            self.locked_users.add(player.user.username)

        kick_notification = PacketFactory.create_packet(
            packet_id=PacketList.DO_VOTE_KICK,
            room=self.room,
            kicked=kicked,
            voted_player_id=player.id
        )
        for remaining_player in self.room.get_all_players():
            if remaining_player.team == player.team and remaining_player != player:
                await remaining_player.user.send(kick_notification.build())

    def get_timestamp(self):
        return int(time.time())
