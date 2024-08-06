import asyncio
from wcps_game.database import get_user_stats, reset_user_kd


class UserStats:
    def __init__(self, username: str):
        self.owner = username
        self.set_defaults()

        self._update_lock = asyncio.Lock()

    def set_defaults(self):
        self.kills = 0
        self.deaths = 0
        self.headshots = 0
        self.bombs_planted = 0
        self.bombs_defused = 0
        self.flags_taken = 0
        self.rounds_played = 0
        self.victories = 0
        self.defeats = 0
        self.vehicles_destroyed = 0

    def reset_stats(self):
        self.set_defaults()

    async def load_stats_from_database(self) -> bool:
        kills_deaths = await get_user_stats(username=self.owner)

        if kills_deaths is not None:
            self.kills = kills_deaths["kills"]
            self.deaths = kills_deaths["deaths"]
            return True
        else:
            return False

    async def update_kills(self, kills: int):
        async with self._update_lock:
            self.kills += kills

    async def update_deaths(self, deaths: int):
        async with self._update_lock:
            self.deaths += deaths

    async def reset_kills_deaths(self):
        async with self._update_lock:
            self.kills = 0
            self.deaths = 0

        await reset_user_kd(username=self.owner)
