import asyncio

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User
    from wcps_core.packets import OutPacket

from wcps_game.game import constants as gconstants
from wcps_game.game.player import Player

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
        is_clanwar: bool = False
    ):

        # Defined at room creation
        self.id = -1
        self.displayname = displayname

        self.channel = master.channel
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

        self.max_players = gconstants.RoomMaximumPlayers.MAXIMUM_PLAYERS[self.channel][max_players]

        # Auto/default settings on room creating
        self.state = gconstants.RoomStatus.WAITING
        self.rounds_setting = 3   # Packet specific
        self.tickets_setting = 3  # Packet specific
        self.rounds = gconstants.ROUND_LIMITS[self.rounds_setting]  # Actual setting
        self.tdm_tickets = gconstants.TDM_LIMITS[self.tickets_setting]  # Actual setting
        self.autostart = False
        self.user_limit = False

        # Set a default map for each mode
        map_defaults = {
            gconstants.ChannelType.CQC: 12,  # Marien
            gconstants.ChannelType.URBANOPS: 0,  # Montana
            gconstants.ChannelType.BATTLEGROUP: 2  # Emblem
        }

        self.current_map = map_defaults[self.channel]

        default_modes = {
            gconstants.ChannelType.CQC: gconstants.GameMode.EXPLOSIVE,
            gconstants.ChannelType.URBANOPS: gconstants.GameMode.TDM,
            gconstants.ChannelType.BATTLEGROUP: gconstants.GameMode.TDM
        }

        self.game_mode = default_modes[self.channel]
        self.ping_limit = gconstants.RoomPingLimit.GREEN

        # Set the user who sent the packet as the default master
        self.master = master
        self.master_slot = 0
        self.master.set_room(self, room_slot=0)

        # Add the master as a player to the dict of players
        this_player = Player(user=self.master, slot=self.master_slot, team=gconstants.Team.DERBARAN)

        # User data for networking
        self.players = dict.fromkeys(range(0, self.max_players))
        self.players[0] = this_player

        self._players_lock = asyncio.Lock()

    def authorize(self, room_id: int):
        self.id = room_id

    def get_players_in_team(self, team_to_count):
        team_count = 0
        for player in self.players:
            if player.team == team_to_count:
                team_to_count += 1

        return team_count

    def get_player_count(self) -> int:
        player_count = 0
        for player in self.players:
            if player is not None:
                player_count += 1

        return player_count

    async def add_player(self, user: "User") -> bool:

        can_join = False

        if self.get_player_count() >= self.max_players or self.user_limit:
            return can_join

        async with self._players_lock:
            player_team = gconstants.Team.DERBARAN

            current_derbaran_players = self.get_players_in_team(gconstants.Team.DERBARAN)
            current_niu_players = self.get_players_in_team(gconstants.Team.NIU)

            if current_derbaran_players > current_niu_players:
                player_team = gconstants.Team.NIU

            # Ok, to find the team, remember that the first half of the slots are always derbaran
            # and the second half, NIU
            if player_team == gconstants.Team.DERBARAN:
                slot_range = range(0, self.max_players / 2)
            else:
                slot_range = range(self.max_players / 2, self.max_players)

            for requested_slot in slot_range:
                if self.players[requested_slot] is None:
                    self.players[requested_slot] = user
                    return True

                return False

    async def remove_player(self, user: "User"):
        if not user.authorized or user.room is None:
            return

        if self.id != user.room.id:  # Is the user somehow removing himself from other room?
            return

        async with self._players_lock:
            if self.players.get(user.room_slot) is None:
                return

            old_player = self.players[user.room_slot]

            # Release the slot and set the player room slot to 0
            self.players[user.room_slot] = None
            user.set_room(None, 0)

            if self.get_player_count() == 0:  # Empty room, destroy it
                self.destroy()
                return

            if old_player.id == self.master_slot:  # This player was the master
                print("Implement new master routine here")

            # Finally, send the room leave packet
            room_leave = PacketFactory.create_packet(
                packet_id=PacketList.DO_EXIT_ROOM,
                user=user,
                room=self,
                old_slot=old_player.id
            )
            await user.send(room_leave.build())

    async def destroy():
        print("Implement me!")

    async def send(self, buffer: "OutPacket"):
        for player in self.players.values():
            if player is not None:
                await player.user.send(buffer)
