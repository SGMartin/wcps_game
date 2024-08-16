from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User
import wcps_game.game.constants as gconstants


class Player:
    def __init__(self, user: "User", slot: int, team: gconstants.Team = gconstants.Team.DERBARAN):
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
        self.branch = gconstants.Classes.ENGINEER   # Eng, medic etc
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
        self.health = 1000
        self.alive = True
        self.vehicle_id = -1
        self.vehicle_seat = -1

    def spawn(self, this_branch: gconstants.Classes):
        self.health = 1000
        self.alive = True
        self.branch = this_branch
        self.vehicle_id = -1
        self.vehicle_seat = - 1

        if self.user.room.game_mode == gconstants.GameMode.EXPLOSIVE:
            self.can_spawn = False

        self.spawn_protection_ticks = 3000
