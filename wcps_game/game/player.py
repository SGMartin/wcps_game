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

        # game data
        self.health = 1000
        self.weapon = 0  # ??
        self.branch = gconstants.Classes.ENGINEER   # Eng, medic etc
        self.vehicle_id = -1
        self.vehicle_seat = -1

        # Add self reference. TODO: Can we trim down self references down the road?
        self.user = user

    def toggle_ready(self):
        self.ready = not self.ready
