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
        self.database_id = db_id
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

    def __init__(self, u: "User"):
        self.owner = u
        self.reset_loadout()

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
            self.equipment_slots = self.get_equipment_slots_from_loadouts(self.loadout)
        else:
            logging.error(f"Failed to load equipment for {self.owner.username}. Going to default")
            self.reset_loadout()

    def reset_loadout(self):
        self.loadout = self.default_loadout
        # set default equipment slots
        self.equipment_slots = self.get_equipment_slots_from_loadouts(self.loadout)

    def get_equipment_slots_from_loadouts(self, loadouts: dict):
        new_equipment_slots = {
            branch: self.parse_equipment_to_slots(loadout_string)
            for branch, loadout_string in loadouts.items()
            }
        return new_equipment_slots

    def parse_equipment_to_slots(self, class_loadout_string: str):
        slot_list = class_loadout_string.split(",")
        slot_list = [weapon if weapon != "^" else None for weapon in slot_list]

        new_slot_dict = {i: None for i in range(len(slot_list))}

        for i, slot_weapon in enumerate(slot_list):
            if i < len(new_slot_dict):
                new_slot_dict[i] = slot_weapon

        return new_slot_dict

    def add_item_to_slot(self, target_class: game_constants.Classes, target_slot: int, item_code: str):
        if item_code is None or len(item_code) != 4:
            logging.error(f"Attempt to add invalid code {item_code}")
            return
        if target_class >= game_constants.MAX_CLASSES:
            logging.error(f"Invalid target class {target_class}")
            return
        if target_slot not in range(0, 8):
            logging.error(f"Invalid target slot {target_slot}")
            return

        self.equipment_slots[target_class][target_slot] = item_code
        self.update_loadout_from_slots(target_class=target_class)

    def remove_item_from_slot(self, target_class: game_constants.Classes, target_slot: int):
        if target_class >= game_constants.MAX_CLASSES:
            logging.error(f"Invalid target class {target_class}")
            return
        if target_slot not in range(0, 8):
            logging.error(f"Invalid target slot {target_slot}")
            return

        self.equipment_slots[target_class][target_slot] = None
        self.update_loadout_from_slots(target_class=target_class)

    def is_equipped_in_class(self, target_class: game_constants.Classes, weapon: str) -> int:
        if target_class >= game_constants.MAX_CLASSES:
            logging.error(f"Invalid target class {target_class}")
            return None

        if weapon is None or len(weapon) != 4:
            logging.error(f"Invalid weapon {weapon}")
            return None

        this_class = self.equipment_slots[target_class]

        for slot, equiped_weapon in enumerate(this_class):
            if weapon == equiped_weapon:
                return slot

        return -1

    def update_loadout_from_slots(self, target_class: game_constants.Classes):
        target_loadout = self.equipment_slots[target_class]
        new_loadout = [weapon if weapon is not None else "^" for weapon in target_loadout.values()]
        new_loadout = ",".join(new_loadout)

        self.loadout[target_class] = new_loadout


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

        # keep a list of expired items for packets
        self.expired_items = []

        # slot data. Slots are available (or not) for all branches of service
        self.available_slots = {
            1: True,
            2: True,
            3: True,
            4: True,
            5: False,
            6: False,
            7: False,
            8: False
            }

    def update_slot_states(self):
        # Define the slot mappings for items CA01 to CA04
        item_slot_mapping = {
            "CA01": 5,  # CA01 unlocks slot 5
            "CA02": 6,  # CA02 unlocks slot 6
            "CA03": 7,  # CA03 unlocks slot 7
            "CA04": 8   # CA04 unlocks slot 8
            }

        # Check if the user is a GOLD premium or higher or has item CA01 to unlock slot 5
        if self.owner.premium > game_constants.Premium.SILVER or self.has_item("CA01"):
            self.available_slots[5] = True

        # Check and update slots based on the item presence
        # TODO: Add logic to enable slots based on px items if needed
        for item, slot in item_slot_mapping.items():
            if self.has_item(item):
                self.available_slots[slot] = True

    def get_slot_string(self):
        slot_status = ["T" if self.available_slots[key] else "F" for key in range(5, 9)]
        slot_string = ",".join(slot_status)
        return slot_string

    def reset(self):
        self.item_list.clear()
        self.expired_items.clear()
        self.inventory_string = self.default_inventory_string
        self.equipment.reset_loadout()

    async def get_inventory_and_equipment_from_db(self):
        success = False

        try:
            database_results = await db.get_user_inventory_and_equipment(
                username=self.owner.username
                )

            await self.load_inventory_equipment_from_db(db_results=database_results)
            success = True

        except pymysql.err.OperationalError as e:
            raise RuntimeError(
                f"DATABASE ERROR: Failed inventory and equipment query for {self.owner.username}"
                ) from e

            success = False
        return success

    async def load_inventory_equipment_from_db(self, db_results: dict):

        if db_results:
            # Attempt to parse loadout
            self.equipment.extract_loadout_from_db_result(db_result=db_results["loadout"])
            await self.extract_inventory_from_db_result(db_results=db_results["inventory"])
        else:
            logging.error(f"Cannot load inventory for {self.owner.username}. Setting defaults")
            self.reset()

        self.format_inventory_from_items()

    async def extract_inventory_from_db_result(self, db_results: list):

        added_items = []

        for item in db_results:
            # TODO: check expiration here
            if len(added_items) <= game_constants.MAX_ITEMS:

                current_epoch_time = int(time.time())
                item_start_date = item["startdate"]
                expire_date = item_start_date + item["leasing_seconds"]

                new_item = Item(
                    slot=0,
                    db_id=item["inventory_id"],
                    item_code=item["inventory_code"],
                    expire_date_seconds=expire_date
                )
                if current_epoch_time >= expire_date:
                    self.expired_items.append(new_item)
                else:
                    added_items.append(new_item)

        self.item_list = added_items

        # call routine on expired items
        if len(self.expired_items) > 0:
            await db.set_inventory_items_expired(self.expired_items)

    def has_item(self, code_to_check: str) -> bool:
        all_codes = [item.item_code for item in self.item_list]
        return code_to_check in all_codes

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

        self.inventory_string = new_item_string
