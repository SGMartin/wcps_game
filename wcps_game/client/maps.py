import logging
from pathlib import Path
import pandas as pd

import wcps_game.game.constants as constants


class MapDatabase:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MapDatabase, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initialize the singleton with the given CSV files.
        """
        try:
            # Get the directory of this script
            self._runtime_dir = Path(__file__).resolve().parent
            self._maps = pd.read_csv(f"{self._runtime_dir}/maps.csv")
            logging.info("Client data files loaded!")
        except FileNotFoundError as e:
            raise RuntimeError(
                "CLIENT MAP DATA ERROR: Cannot load client data tables"
            ) from e

    @property
    def map_data(self):
        return self._maps

    def get_map_channels(self, map_id: int) -> dict:
        available_channels = {
            constants.ChannelType.CQC: False,
            constants.ChannelType.URBANOPS: False,
            constants.ChannelType.BATTLEGROUP: False,
        }
        if map_id in self._maps.index:
            available_channels[constants.ChannelType.CQC] = self._maps.loc[
                self._maps["map_id"] == map_id, "cqc"
            ].values[0]
            available_channels[constants.ChannelType.URBANOPS] = self._maps.loc[
                self._maps["map_id"] == map_id, "uo"
            ].values[0]
            available_channels[constants.ChannelType.BATTLEGROUP] = self._maps.loc[
                self._maps["map_id"] == map_id, "bg"
            ].values[0]

        return available_channels

    def get_map_modes(self, map_id: int) -> dict:
        available_modes = {
            constants.GameMode.EXPLOSIVE: False,
            constants.GameMode.FFA: False,
            constants.GameMode.TDM: False,
            constants.GameMode.CONQUEST: False,
        }

        if map_id in self._maps.index:
            available_modes[constants.GameMode.EXPLOSIVE] = self._maps.loc[
                self._maps["map_id"] == map_id, "explosive"
            ].values[0]
            available_modes[constants.GameMode.FFA] = self._maps.loc[
                self._maps["map_id"] == map_id, "ffa"
            ].values[0]
            available_modes[constants.GameMode.TDM] = self._maps.loc[
                self._maps["map_id"] == map_id, "deathmatch"
            ].values[0]
            available_modes[constants.GameMode.CONQUEST] = self._maps.loc[
                self._maps["map_id"] == map_id, "conquest"
            ].values[0]

        return available_modes

    def get_map_status(self, map_id: int) -> bool:
        status = False
        if map_id in self._maps.index:
            status = self._maps.loc[self._maps["map_id"] == map_id, "active"].values[0]
        return status

    def get_map_premium(self, map_id: int) -> int:
        premium = None
        premium_dict = {
            "Free": constants.Premium.F2P,
            "Bronze": constants.Premium.BRONZE,
            "Silver": constants.Premium.SILVER,
            "Gold": constants.Premium.GOLD,
        }
        if map_id in self._maps.index:
            premium = premium_dict[
                self._maps.loc[self._maps["map_id"] == map_id, "premium"].values[0]
            ]

        return premium
