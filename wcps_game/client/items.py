import logging
from pathlib import Path

import pandas as pd


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
