from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.player import Player


class GroundItem():
    def __init__(self, owner: "Player", code: str):
        self.id = None
        self.owner = owner
        self.code = code
        self.used = False

    def place(self, room_id: int):
        self.id = room_id

    def activate(self):
        if not self.used:
            self.used = True

    def can_activate(self):
        return not self.used
