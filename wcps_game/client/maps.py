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
            dtypes = {
                "map_id": "int",
                "map_name": "str",
                "cqc": "bool",
                "uo": "bool",
                "bg": "bool",
                "explosive": "bool",
                "deathmatch": "bool",
                "ffa": "int",
                "conquest": "bool",
                "premium": "str",
                "active": "bool",
                "flags": "int",
                "spawn_flags": "str"
            }
            self._maps = pd.read_csv(f"{self._runtime_dir}/maps.csv", dtype=dtypes)

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

    def get_first_map_for_mode(self, game_mode: int, channel: int) -> int:
        modes = {
            constants.GameMode.EXPLOSIVE: "explosive",
            constants.GameMode.FFA: "ffa",
            constants.GameMode.TDM: "deathmatch",
            constants.GameMode.CONQUEST: "conquest"
        }
        channels = {
            constants.ChannelType.CQC: "cqc",
            constants.ChannelType.URBANOPS: "uo",
            constants.ChannelType.BATTLEGROUP: "bg"
        }

        this_game_mode = modes[game_mode]
        this_channel = channels[channel]

        available_maps = self._maps.loc[
            (self._maps[this_game_mode] > 0) & (self._maps[this_channel]),
            "map_id"
            ].sort_values(ascending=True).iloc[0]

        return available_maps

    def get_spawn_flags(self, map_id: int) -> dict:
        flags = {
            constants.Team.DERBARAN: None,
            constants.Team.NIU: None
        }
        if map_id in self._maps.index:
            spawn_flags = self._maps.loc[self._maps["map_id"] == map_id, "spawn_flags"].values[0]
            spawn_flags = spawn_flags.split(",")

            flags[constants.Team.DERBARAN] = int(spawn_flags[0])
            flags[constants.Team.NIU] = int(spawn_flags[1])

        return flags

    def get_flag_number(self, map_id: int) -> int:
        max_flags = None

        if map_id in self._maps.index:
            max_flags = self._maps.loc[self._maps["map_id"] == map_id, "flags"].values[0]

        return max_flags

    # FFA maps come in two sizes, the FFA "Scale" of the client's MapInfo (column "ffa"): small (8), the CQC
    # maps, and medium (16), four UO maps kept with no vehicles for this. The client's map selector offers
    # small maps while the room has up to 8 players and medium ones from 9 on, whatever the room's channel.
    FFA_SMALL = 8
    FFA_MEDIUM = 16

    @classmethod
    def ffa_scale_for_players(cls, player_count: int) -> int:
        return cls.FFA_SMALL if player_count < 9 else cls.FFA_MEDIUM

    def get_ffa_scale(self, map_id: int) -> int:
        """FFA size of the map (8 or 16), 0 if it has no FFA."""
        rows = self._maps.loc[self._maps["map_id"] == map_id, "ffa"]
        return int(rows.values[0]) if len(rows) else 0

    def get_first_ffa_map(self, scale: int) -> int:
        """Active FFA map of this size with the lowest id: where the room goes when it changes size."""
        maps = self._maps.loc[(self._maps["ffa"] == scale) & (self._maps["active"]), "map_id"]
        return int(maps.min())
