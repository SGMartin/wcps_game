import wcps_game.game.constants as game_constants

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from wcps_game.game.game_server import User


class Equipment:
    default_loadout = {
            game_constants.Classes.ENGINEER: "DA02,DB01,DF01,DR01,^,^,^,^",
            game_constants.Classes.MEDIC:  "DA02,DB01,DF01,DQ01,^,^,^,^",
            game_constants.Classes.SNIPER:  "DA02,DB01,DG05,DN01,^,^,^,^",
            game_constants.Classes.ASSAULT: "DA02,DB01,DC02,DN01,^,^,^,^",
            game_constants.Classes.HEAVY: "DA02,DB01,DJ01,DL01,^,^,^,^"

        }

    available_slots = {1: True, 2: True, 3: True, 4: True, 5: False, 6: False, 7: False, 8: False}

    def __init__(self, u: "User"):
        self.owner = u

        # Set slots
        self.update_slot_states()

    def update_slot_states(self):
        if self.owner.premium > game_constants.Premium.SILVER:
            # Only GOLD premium users had 5th slot enabled by default
            self.available_slots[5] = True
            # TODO: check if user has items:
            # CA01-4 (slots 5h to 8th) even if by default they were not in CP1

    def get_slot_string(self):
        slot_status = ["T" if self.available_slots[key] else "F" for key in range(5, 9)]
        slot_string = ",".join(slot_status)
        return slot_string



