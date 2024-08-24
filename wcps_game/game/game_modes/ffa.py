import asyncio

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room

from wcps_game.game.base_game_mode import BaseGameMode

import wcps_game.game.constants as gconstants


class FFA(BaseGameMode):
    def __init__(self):
        super().__init__(
            id=gconstants.GameMode.FFA,
            name="Free for all"
        )

        self.current_winner_kills = 0
        self.max_kills = 0
        self.b_spawn_point = 0
        self.bln_first_spawn = True

        # Initialize an asyncio Lock object for thread safety
        self._spawn_lock = asyncio.Lock()

    def initialize(self, room: "Room"):
        super().initialize(room)

        self.max_kills = 10 + (room.tickets_setting * 5)
        self.room.down_tick = 3600000  # TODO: this should be configurable
        self.initialized = True
        self.freeze_tick = False
        self.bln_first_spawn = True

    def winner(self):
        return gconstants.Team.NONE  # No teams in FFA

    async def process(self):
        if self.room.down_ticks <= 0 or self.room.get_player_count() <= 1:
            await self.room.end_game(self.winner())

    def is_goal_reached(self):
        return self.current_winner_kills >= self.max_kills

    # FFA does not have rounds
    def current_round_derbaran(self):
        return 0

    # FFA does not have rounds
    def current_round_niu(self):
        return 0

    # FFA uses these two to keep track of the top killer kills
    def scoreboard_derbaran(self):
        return self.max_kills

    def scoreboard_niu(self):
        return self.current_winner_kills

    async def get_spawn_id(self):
        async with self._spawn_lock:
            if not self.bln_first_spawn:
                self.b_spawn_point += 1

                if self.b_spawn_point >= 20:  # FFA on CQC has 20 spawn points max (0-19)
                    self.b_spawn_point = 0
            else:
                self.b_spawn_point = 0
                self.bln_first_spawn = False

        return self.b_spawn_point

    async def on_death(self, killer, victim):
        if killer is not None:
            if killer.kills > self.current_winner_kills:
                self.current_winner_kills = killer.kills

            if self.current_winner_kills >= self.max_kills:
                await self.room.end_game(gconstants.Team.NONE)

    async def on_flag_capture(self, player, flag_status):
        raise NotImplementedError

    async def on_suicide(self, player):
        pass
