import asyncio

from wcps_game.game.constants import Team, VehicleClass


class Vehicle():
    def __init__(self, health: int, code: str, vehicle_class: VehicleClass = VehicleClass.GROUND):

        self.type = vehicle_class
        self.seats = {}
        self.code = code
        self.max_health = self.health = health

        # The ID of the vehicle (set by map)
        self.id = None
        self.spawn_time = None
        self.team = Team.NONE

        # Coordinates for the vehicle position
        self.X = 0
        self.Y = 0
        self.Z = 0

        self._vehicle_lock = asyncio.Lock()

    def set_map_id(self, map_id: int):
        self.id = map_id

    def set_team(self, new_team: Team):
        self.team = new_team

    def set_spawn_time(self, spawn_time: int):
        self.spawn_time = spawn_time

    def update_position(self, coords: dict):
        self.X = coords["X"]
        self.Y = coords["Y"]
        self.Z = coords["Z"]

    async def join_vehicle(self, new_pilot) -> bool:
        async with self._vehicle_lock:
            if new_pilot.team != self.team and self.team != Team.NONE:
                return

            # Always start from the first available seat
            for seat in self.seats.values():
                if await seat.add_player(new_pilot):
                    self.set_team(new_team=new_pilot.team)
                    return True

            return False


class VehicleSeat():
    def __init__(self, seat_id: int):

        # ID in the vehicle. Starts from 0
        self.id = seat_id

        # Player data
        self.player = None
        self.player_id = -1

        # any weapon has a code in items.bin (equipment class)
        self.main_weapon_code = ""
        self.sub_weapon_code = ""

        # Current recharges for both weapons
        self.main_weapon_magazine = 0
        self.sub_weapon_magazine = 0

        # Current amo for each weapon
        self.main_weapon_ammo = 0
        self.sub_weapon_ammo = 0

        # Max recharges size for both weapons
        self.main_weapon_max_magazine = 0
        self.sub_weapon_max_magazine = 0

        # Max ammo for each weapon
        self.main_weapon_max_ammo = 0
        self.sub_weapon_max_ammo = 0

        # Lock for race conditions
        self._seat_lock = asyncio.Lock()

    def can_seat(self):
        if self.player is None:
            return True
        else:
            return False

    def add_main_weapon(self, code: str, max_ammo: int, max_magazines: int):
        self.main_weapon_code = code
        self.main_weapon_max_ammo = max_ammo
        self.main_weapon_max_magazine = max_magazines

        self.rechage_weapons()

    def add_sub_weapon(self, code: str, max_ammo: int, max_magazines: int):
        self.sub_weapon_code = code
        self.sub_weapon_max_ammo = max_ammo
        self.sub_weapon_max_magazine = max_magazines

        self.rechage_weapons()

    def rechage_weapons(self):
        # Main weapon
        self.main_weapon_ammo = self.main_weapon_max_ammo
        self.main_weapon_magazine = self.main_weapon_max_magazine
        # Sub weapon
        self.sub_weapon_ammo = self.sub_weapon_max_ammo
        self.sub_weapon_magazine = self.sub_weapon_max_magazine

    async def add_player(self, player) -> bool:
        async with self._seat_lock:
            if self.can_seat():
                self.player = player
                self.player_id = player.id
                return True
            else:
                return False

    async def remove_player(self, player):
        async with self._seat_lock:
            if self.player is not None:
                self.player = None
                self.player_id = -1
