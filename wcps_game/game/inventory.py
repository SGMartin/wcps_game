import pymysql
import logging
from datetime import datetime, timedelta, timezone
import time
import wcps_game.game.constants as game_constants
import wcps_game.database as db

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from wcps_game.game.game_server import User


class Item:
    def __init__(self, slot, db_id: int, item_code: str, expire_date_seconds: int):
        self.slot = slot
        self.database_id = db_id  # TODO: haven't yet decided If I'm using this one
        self.item_code = item_code.upper()
        self.expire_date = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=expire_date_seconds)
        self.amount = 0
        self.equipped = [-1] * game_constants.MAX_CLASSES

        if self.item_code.startswith("D"):
            self.type = game_constants.ItemType.WEAPON
        else:
            self.type = game_constants.ItemType.OTHER


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
            self.extract_loadout_from_db_result(database_loadout)
        except pymysql.err.OperationalError as e:
            raise RuntimeError(
                f"DATABASE ERROR: Cannot complete loadout query for {self.owner.username}"
                ) from e

            success = False
        return success

    def extract_loadout_from_db_result(self, db_result: dict):
        if db_result:
            loadout = {
                game_constants.Classes.ENGINEER: db_result["engineer"],
                game_constants.Classes.MEDIC: db_result["medic"],
                game_constants.Classes.SNIPER: db_result["sniper"],
                game_constants.Classes.ASSAULT: db_result["assault"],
                game_constants.Classes.HEAVY: db_result["heavy_trooper"]
            }
            self.loadout = loadout
        else:
            logging.error(f"Failed to load equipment for {self.owner.username}. Going to default")
            self.reset_loadout()

    def reset_loadout(self):
        self.loadout = self.default_loadout


class Inventory:
    default_inventory_string = ""
    for i in range(32):
        if i == 0:
            default_inventory_string = "^"
        else:
            default_inventory_string += ",^"

    def __init__(self, user: "User"):
        self.owner = user

        self.item_list = []
        self.inventory_string = self.default_inventory_string

        # load loadout data from here
        self.equipment = Equipment(self.owner)

    def reset(self):
        self.item_list = []
        self.inventory_string = self.default_inventory_string
        self.equipment.reset_loadout()

    async def get_inventory_and_equipment_from_db(self):
        success = False

        try:
            database_results = await db.get_user_inventory_and_equipment(
                username=self.owner.username
                )

            self.load_inventory_equipment_from_db(db_results=database_results)
            success = True

        except pymysql.err.OperationalError as e:
            raise RuntimeError(
                f"DATABASE ERROR: Failed inventory and equipment query for {self.owner.username}"
                ) from e

            success = False
        return success

    def load_inventory_equipment_from_db(self, db_results: dict):

        if db_results:
            # Attempt to parse loadout
            self.equipment.extract_loadout_from_db_result(db_result=db_results["loadout"])
            self.extract_inventory_from_db_result(db_results=db_results["inventory"])
        else:
            logging.error(f"Cannot load inventory for {self.owner.username}. Setting defaults")
            self.reset()

        self.format_inventory_from_items()

    def extract_inventory_from_db_result(self, db_results: list):

        added_items = []

        for item in db_results:
            # TODO: check expiration here
            if len(added_items) <= game_constants.MAX_ITEMS:
                current_epoch_time = int(time.time())
                item_start_date = item["startdate"]
                print(item_start_date)
                print(item["leasing_seconds"])
                expire_date = item_start_date + item["leasing_seconds"]
                print(expire_date)
                new_item = Item(
                    slot=0,
                    db_id=item["inventory_id"],
                    item_code=item["inventory_code"],
                    expire_date_seconds=expire_date
                )
                added_items.append(new_item)

        self.item_list = added_items

    def format_inventory_from_items(self):
        new_item_string = ""

        # Empty inventory
        if not self.item_list:
            return self.default_inventory_string

        item_string_list = [
            f"{item.item_code}-{item.type}-0-{item.expire_date.strftime("%y%m%d%H")}-{item.amount}" for item in self.item_list
            ]
        new_item_string = ",".join(item_string_list)

        # Fill with ^ until completion
        missing_item_slots = game_constants.MAX_ITEMS - len(self.item_list)

        for i in range(0, missing_item_slots):
            new_item_string = f"{new_item_string},^"

        print(f"FINAL ITEM STRING {new_item_string}")
        self.inventory_string = new_item_string