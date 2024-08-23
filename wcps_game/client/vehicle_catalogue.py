import copy
import logging
from pathlib import Path
from string import ascii_uppercase

import pandas as pd

from wcps_game.game.vehicle import Vehicle, VehicleSeat
from wcps_game.game.constants import VehicleClass


class VehicleCatalogue:
    _instance = None

    # A - I vehicle subclasses (see items settings in items.bin) are ground based
    code_to_vehicle_class = {
        letter: VehicleClass.GROUND for letter in ascii_uppercase[:9]
    }
    code_to_vehicle_class["J"] = VehicleClass.AIRCRAFT
    code_to_vehicle_class["K"] = VehicleClass.AIRCRAFT
    code_to_vehicle_class["L"] = VehicleClass.SHIP
    code_to_vehicle_class["M"] = VehicleClass.SHIP

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._vehicles = {}  # Initialize the vehicle dictionary
            cls._instance._initialize_catalogue()  # Initialize the catalogue
            cls._instance._initialize_map_data()  # Initialize map data
        return cls._instance

    def _initialize_map_data(self):
        # Load map data
        self._runtime_dir = Path(__file__).resolve().parent
        map_data_df = pd.read_csv(f"{self._runtime_dir}/map_vehicles.csv")
        self._map_data = map_data_df

    def _initialize_catalogue(self):
        # Load data tables
        self._runtime_dir = Path(__file__).resolve().parent
        vehicles_df = pd.read_csv(f"{self._runtime_dir}/vehicles.csv")

        vehicle_codes = vehicles_df["code"].unique().tolist()

        for veh_code in vehicle_codes:
            # Create Vehicle instance
            vehicle_df = vehicles_df[vehicles_df["code"] == veh_code]
            health = int(vehicle_df["health"].values[0])
            vehicle_class = self.code_to_vehicle_class.get(
                veh_code[1], VehicleClass.GROUND
            )

            this_vehicle = Vehicle(
                health=health, code=veh_code, vehicle_class=vehicle_class
            )

            # Create seats and weapons
            vehicle_seats = vehicle_df.groupby("seat_id")
            for seat_id, group in vehicle_seats:
                this_seat = VehicleSeat(seat_id=seat_id)

                # Handle weapons for the seat
                if len(group) > 0:
                    main_weapon_details = group.iloc[0]  # First weapon
                    this_seat.add_main_weapon(
                        code=main_weapon_details["weapon_code"],
                        max_ammo=main_weapon_details["weapon_ammo"],
                        max_magazines=main_weapon_details["weapon_magazine"],
                    )
                if len(group) > 1:
                    sub_weapon_details = group.iloc[1]  # Second weapon
                    this_seat.add_sub_weapon(
                        code=sub_weapon_details["weapon_code"],
                        max_ammo=sub_weapon_details["weapon_ammo"],
                        max_magazines=sub_weapon_details["weapon_magazine"],
                    )
                this_vehicle.seats[seat_id] = this_seat

            self._vehicles[veh_code] = this_vehicle

        logging.info(f"Initialized {len(self._vehicles)} active vehicles")

    def get_vehicle(self, code):
        # Return a deep copy of the vehicle instance
        vehicle = self._vehicles.get(code)
        if vehicle:
            return copy.deepcopy(vehicle)
        return None

    def get_vehicles_for_map(self, map_id: int) -> dict:
        # Filter map data for the given map_id
        map_vehicles = self._map_data[self._map_data["map_id"] == map_id]

        # Create a dict to store deep copies of vehicles
        vehicles_for_map = {}

        for _, row in map_vehicles.iterrows():
            vehicle_code = row["vehicle_code"]
            vehicle = self.get_vehicle(vehicle_code)

            if vehicle:
                # Extract and validate the vehicle ID
                try:
                    vehicle_map_id = int(row["vehicle_id"])
                except ValueError:
                    logging.warning(
                        f"Invalid vehicle_id: {row['vehicle_id']}. Skipping row."
                    )
                    continue

                # Set map ID for the vehicle
                vehicle.set_map_id(map_id=vehicle_map_id)

                # Update vehicle with its specific map data (position and spawn time)
                try:
                    coords = row["coords"].split("/")
                    if len(coords) != 3:
                        raise ValueError("Invalid coordinates format")
                    x, y, z = map(float, coords)
                except (ValueError, IndexError) as e:
                    logging.error(
                        f"Error parsing coordinates '{row['coords']}': {e}. Setting  to 0,0,0."
                    )
                    x, y, z = 0.0, 0.0, 0.0

                vehicle.update_position({"X": x, "Y": y, "Z": z})
                vehicle.set_spawn_time(row["spawn_interval"])

                # Store the vehicle in the dictionary with its map ID
                vehicles_for_map[vehicle_map_id] = vehicle

        return vehicles_for_map
