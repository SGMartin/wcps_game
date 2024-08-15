import logging
from pathlib import Path
import pandas as pd


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
