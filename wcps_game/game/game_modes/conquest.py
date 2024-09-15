import asyncio

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room

from wcps_game.config import settings
from wcps_game.game.base_game_mode import BaseGameMode

import wcps_game.game.constants as gconstants

# Apr-2007
# New Game Mode: Conquest

# Conquest is an objective, team-based battle where teams fight for control of a map by capturing
# key points throughout the map. At the beginning of a Conquest game, both teams start with a
# base score which ticks down every second. The only way to slow down the clock is to capture bases
# and defend them with your life. Teamwork is the key in this mode, as teams will need to work
# together to advance and overtake their opponents’ key strategic points. Creating a Conquest
# room requires a Premium account. All players are able to join public Conquest games
# created by Premium members.
# Note: At the start of the match, all bases are open for capture,
# with the exception of the enemy’s main base flag.
# This flag becomes available for capture after three minutes.
# An in-game timer has been added to display this information.


class Conquest(BaseGameMode):
    def __init__(self):
        super().__init__(
            id=gconstants.GameMode.CONQUEST,
            name="Conquest"
        )

        # Initialize an asyncio Lock object for thread safety
        self._spawn_lock = asyncio.Lock()

    async def initialize(self, room: "Room"):
        await super().initialize(room)

        # TODO: make this configurable
        self.derbaran_tickets = self.niu_tickets = 999
        self.derbaran_slowdown = self.niu_slowdown = 0
        self.derbaran_flags = self.niu_flags = 1
        # This one should not be configured as they added a timer in the client which is
        # hard set to 5 minutes
        self.main_flag_protection_time = 300000
        self.room.down_ticks = settings().game_time_limit * 1000
        self.time_elapsed = self.room.down_ticks
        self.initialized = True
        self.freeze_tick = False

    def winner(self):

        if self.niu_flags == 0 or self.derbaran_flags == 0:
            if self.niu_flags > self.derbaran_flags:
                return gconstants.Team.NIU
            elif self.derbaran_flags > self.niu_flags:
                return gconstants.Team.DERBARAN
            else:
                return gconstants.Team.NONE

        if self.derbaran_tickets == self.niu_tickets:
            return gconstants.Team.NONE
        else:
            if self.derbaran_tickets > self.niu_tickets:
                return gconstants.Team.DERBARAN
            else:
                return gconstants.Team.NIU

    async def process(self):
        if self.room.down_ticks <= 0:
            await self.room.end_game(self.winner())
            return

        derbaran_players = self.room.get_player_count_in_team(gconstants.Team.DERBARAN)
        niu_players = self.room.get_player_count_in_team(gconstants.Team.NIU)

        if niu_players == 0:
            await self.room.end_game(gconstants.Team.DERBARAN)
        elif derbaran_players == 0:
            await self.room.end_game(gconstants.Team.NIU)

        if self.time_elapsed - self.room.down_ticks == 1000:
            self.update_tickets()
            self.time_elapsed = self.room.down_ticks

        # Allow the capture of the main flags
        if self.room.up_ticks == self.main_flag_protection_time and self.room.spawn_flags:
            self.room.spawn_flags.clear()

    def update_tickets(self):
        if self.niu_slowdown == 0:
            self.niu_tickets = max(0, self.niu_tickets - 1)
            self.niu_slowdown = self.niu_flags
        else:
            self.niu_slowdown -= 1

        if self.derbaran_slowdown == 0:
            self.derbaran_tickets = max(0, self.derbaran_tickets - 1)
            self.derbaran_slowdown = self.derbaran_flags
        else:
            self.derbaran_slowdown -= 1

    def is_goal_reached(self):
        if self.derbaran_tickets == 0 or self.niu_tickets == 0:
            return True
        elif self.derbaran_flags == 0 or self.niu_flags == 0:
            return True
        else:
            return False

    async def on_death(self, killer, victim):
        if victim.team == gconstants.Team.DERBARAN:
            self.derbaran_tickets -= 1
        else:
            self.niu_tickets -= 1

    async def on_suicide(self, player):
        if player.team == gconstants.Team.DERBARAN:
            self.derbaran_tickets -= 1
        else:
            self.niu_tickets -= 1

    async def on_flag_capture(self, player, flag_status):
        if flag_status == -1:  # neutral flag
            if player.team == gconstants.Team.DERBARAN:
                self.derbaran_flags += 1
            else:
                self.niu_flags += 1

        if player.team == gconstants.Team.DERBARAN:
            self.niu_tickets -= 1
        else:
            self.derbaran_tickets -= 1

    def current_round_derbaran(self):
        return 0

    def current_round_niu(self):
        return 0

    def scoreboard_derbaran(self):
        return self.derbaran_tickets

    def scoreboard_niu(self):
        return self.niu_tickets
