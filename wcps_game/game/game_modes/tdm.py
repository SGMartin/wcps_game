import asyncio

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room

from wcps_game.game.base_game_mode import BaseGameMode

import wcps_game.game.constants as gconstants


class TDM(BaseGameMode):
    def __init__(self):
        super().__init__(
            id=gconstants.GameMode.TDM,
            name="Team Death Match"
        )

        # Initialize an asyncio Lock object for thread safety
        self._spawn_lock = asyncio.Lock()

    def initialize(self, room: "Room"):
        super().initialize(room)

        self.derbaran_tickets = self.niu_tickets = self.room.tdm_tickets

        self.room.down_tick = 3600000  # TODO: this should be configurable
        self.initialized = True
        self.freeze_tick = False

    def winner(self):
        if self.derbaran_tickets == self.niu_tickets:
            return gconstants.Team.NONE

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

    def is_goal_reached(self):
        if self.derbaran_tickets == 0 or self.niu_tickets == 0:
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
        if player.team == gconstants.Team.DERBARAN:
            self.niu_tickets -= 1
        else:
            self.derbaran_tickets -= 1

    def current_round_derbaran(self):
        return 0

    # FFA does not have rounds
    def current_round_niu(self):
        return 0

    # FFA uses these two to keep track of the top killer kills
    def scoreboard_derbaran(self):
        return self.derbaran_tickets

    def scoreboard_niu(self):
        return self.niu_tickets
