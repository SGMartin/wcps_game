import logging
from pathlib import Path
import pandas as pd

from wcps_game.game.constants import DamageTypes


class ItemDatabase:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ItemDatabase, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initialize the singleton with the given CSV files.
        """
        try:
            # Get the directory of this script
            self._runtime_dir = Path(__file__).resolve().parent
            self._items = pd.read_csv(f"{self._runtime_dir}/items.csv")
            self._item_shop = pd.read_csv(f"{self._runtime_dir}/item_shop.csv")
            self._weapons = pd.read_csv(f"{self._runtime_dir}/weapon_damage.csv")
            logging.info("Client data files loaded!")
        except FileNotFoundError as e:
            raise RuntimeError(
                "CLIENT DATA ERROR: Cannot load client data tables"
            ) from e

    @property
    def item_data(self):
        return self._items

    @property
    def shop_data(self):
        return self._item_shop

    @property
    def weapon_data(self):
        return self._weapons

    def item_exists(self, code: str):
        return self._items["code"].eq(code).any()

    def is_active(self, code: str):
        is_active = False
        if self.item_exists(code=code):
            return self._items.loc[self._items["code"] == code, "active"].values[0]
        else:
            return is_active

    def is_buyable(self, code: str) -> bool:
        if self.item_exists(code=code):
            value = self._item_shop.loc[
                self._item_shop["code"] == code, "is_buyable"
            ].values[0]
            return value

    def requires_premium(self, code: str) -> bool:
        if self.item_exists(code=code):
            prem_val = self._item_shop.loc[
                self._item_shop["code"] == code, "required_premium"
            ].values[0]

        if prem_val == -1:
            return False
        else:
            return True

    def get_required_level(self, code: str) -> int:
        if self.item_exists(code=code):
            req_lvl = self._item_shop.loc[
                self._item_shop["code"] == code, "required_level"
            ].values[0]
            return int(req_lvl)

    def get_weapon_costs(self, code: str) -> list:
        if self.item_exists(code=code) and self.is_buyable(code=code):
            cost_str = self._item_shop.loc[
                self._item_shop["code"] == code, "cost"
            ].values[0]
            cost_list = [int(cost) for cost in cost_str.split(",")]
            return cost_list

        return []

    def is_weapon(self, code: str) -> bool:
        return self._weapons["code"].eq(code).any()

    def get_weapon_power(self, code: str) -> int:
        return self._weapons.loc[self._weapons["code"] == code, "power"].values[0]

    def get_weapon_damage_class(self, code: str, damage_class: DamageTypes):
        columns_to_look = {
            DamageTypes.INFANTRY: "personal",
            DamageTypes.GROUND: "surface",
            DamageTypes.AIRCRAFT: "air",
            DamageTypes.SHIP: "ship"
        }
        column_to_look = columns_to_look[damage_class]

        if self.item_exists(code=code) and self.is_weapon(code=code):
            damages = self._weapons.loc[self._weapons["code"] == code, column_to_look].values[0]
            damages = [int(d) for d in damages.split(",")]
            return damages
        else:
            return None
