import math

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User
import wcps_game.game.constants as gconstants


class Player:
    def __init__(
        self, user: "User", slot: int, team: gconstants.Team = gconstants.Team.DERBARAN
    ):
        self.id = slot

        # Lobby data
        self.team = team
        self.ready = False
        self.state = gconstants.RoomStatus.WAITING  # same as room :)

        self.user = user

        self.reset_game_state()

    def toggle_ready(self):
        self.ready = not self.ready

    def reset_game_state(self):

        # game data
        self.health = 1000
        self.spawn_protection_ticks = 3000
        self.weapon = 0
        self.branch = gconstants.Classes.ENGINEER  # Eng, medic etc
        self.vehicle_id = -1
        self.vehicle_seat = -1
        self.alive = True

        # game stats
        self.assists = 0
        self.bombs_defused = 0
        self.bombs_planted = 0
        self.deaths = 0
        self.flags_taken = 0
        self.headshots = 0
        self.kills = 0
        self.losses = 0
        self.money_earned = 0
        self.points = 0
        self.vehicles_destroyed = 0
        self.wins = 0
        self.xp_earned = 0

    def round_start(self):
        self.can_spawn = True
        self.state = gconstants.RoomStatus.PLAYING
        self.health = 1000
        self.alive = True
        self.vehicle_id = -1
        self.vehicle_seat = -1

    def spawn(self, this_branch: gconstants.Classes):
        self.health = 1000
        self.alive = True
        self.branch = this_branch
        self.vehicle_id = -1
        self.vehicle_seat = -1

        if self.user.room.game_mode == gconstants.GameMode.EXPLOSIVE:
            self.can_spawn = False

        self.spawn_protection_ticks = 3000

    async def add_kills(self, headshot: bool = False):
        self.kills += 1
        await self.user.stats.update_kills(kills=1)

        if headshot:
            self.headshots += 1

        self.points += 5

    async def add_deaths(self):
        self.deaths += 1
        self.health = 0
        self.alive = False
        self.vehicle_id = -1
        self.vehicle_seat - 1
        await self.user.stats.update_deaths(deaths=1)

    async def end_game(self):
        self.vehicle_id = -1
        self.vehicle_seat = -1

        # Calculate the rewards :)
        if self.points < 0:
            self.points = 0

        # CQC bonus
        if self.user.room.game_mode == gconstants.GameMode.EXPLOSIVE:
            self.points = self.points * 2

        # Premium bonus
        premium_bonus = {
            gconstants.Premium.F2P: 1,
            gconstants.Premium.BRONZE: 1.2,
            gconstants.Premium.SILVER: 1.3,
            gconstants.Premium.GOLD: 1.5,
        }

        # Super master bonus
        is_super_room = self.user.room.supermaster

        is_super_master = (
            self.user.inventory.has_item("CC02")
            and is_super_room
            and self.id == self.user.room.master_slot
        )

        # Item bonus
        item_xp_rate = 0
        item_money_rate = 0

        # CD01 = 30% exp UP
        item_xp_rate = (
            item_xp_rate + 0.3 if self.user.inventory.has_item("CD01") else item_xp_rate
        )
        # CD02 = 20% exp UP
        item_xp_rate = (
            item_xp_rate + 0.2 if self.user.inventory.has_item("CD02") else item_xp_rate
        )
        # CC05 = double up
        item_xp_rate = (
            item_xp_rate + 0.25
            if self.user.inventory.has_item("CC05")
            else item_xp_rate
        )

        # CE01 = 20% dinar up
        item_money_rate = (
            item_money_rate + 0.2
            if self.user.inventory.has_item("CE01")
            else item_money_rate
        )
        # CE02 = 30% dinar up
        item_money_rate = (
            item_money_rate + 0.3
            if self.user.inventory.has_item("CE02")
            else item_money_rate
        )
        # CC05 = double up
        item_money_rate = (
            item_money_rate + 0.25
            if self.user.inventory.has_item("CC05")
            else item_money_rate
        )

        final_xp_rate = premium_bonus[self.user.premium] + item_xp_rate
        final_money_rate = 1 + item_money_rate

        if is_super_master:
            final_xp_rate += 0.05
            final_money_rate += 0.1

        if not is_super_master and is_super_room:
            final_xp_rate += 0.05

        xp_earned = 20 + self.points * 4 * final_xp_rate
        money_earned = 50 + self.points * 3 * final_money_rate

        # TODO: add global rates here or event rates :)
        xp_earned = math.ceil(xp_earned)
        money_earned = math.ceil(money_earned)

        self.xp_earned = xp_earned
        self.money_earned = money_earned

        if self.id == self.user.room.master_slot:
            self.ready = True
        else:
            self.ready = False

        # Call user end game here
        await self.user.end_game(xp_earned=self.xp_earned, money_earned=self.money_earned)
