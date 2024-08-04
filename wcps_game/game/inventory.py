import pymysql
import logging

import wcps_game.game.constants as game_constants
import wcps_game.database as db

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

        # set loadout
        self.loadout = self.default_loadout

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

    async def get_loadout_from_database(self) -> bool:
        success = False

        try:
            database_loadout = await db.get_user_inventory_and_equipment(self.owner.username)
            success = True
        except pymysql.err.OperationalError as e:
            raise RuntimeError(
                f"DATABASE ERROR: Cannot complete loadout query for {self.owner.username}"
                ) from e
            
            success = False

        if database_loadout:
            loadout = {
                game_constants.Classes.ENGINEER: database_loadout["engineer"],
                game_constants.Classes.MEDIC: database_loadout["medic"],
                game_constants.Classes.SNIPER: database_loadout["sniper"],
                game_constants.Classes.ASSAULT: database_loadout["assault"],
                game_constants.Classes.HEAVY: database_loadout["heavy_trooper"]
            }
            self.loadout = loadout
        else:
            logging.error(f"Failed to load equipment for {self.owner.username}. Going to default")
            self.loadout = self.default_loadout

        return success
