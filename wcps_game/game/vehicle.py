import asyncio

from wcps_game.game.constants import Team, VehicleClass


class Vehicle():
    def __init__(self, health: int, code: str, vehicle_class: VehicleClass = VehicleClass.GROUND):

        self.type = vehicle_class
        self.seats = {}
        self.code = code
        self.max_health = self.health = health
        self.spawn_protection_ticks = 0

        # The ID of the vehicle (set by map)
        self.id = None
        self.spawn_time = None
        self.team = Team.NONE

        # Coordinates for the vehicle position
        self.X = 0
        self.Y = 0
        self.Z = 0
        # Euler
        self.angular_X = 0
        self.angular_Y = 0
        self.angular_Z = 0
        # WarRock client stuff. It changes when a player leaves the veh. and we update the
        # position and euler
        self.update_string = ""

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

    def update_angles(self, euler: dict):
        self.angular_X = euler["X"]
        self.angular_Y = euler["Y"]
        self.angular_Z = euler["Z"]

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

    async def leave_vehicle(self, old_pilot) -> bool:
        async with self._vehicle_lock:
            seat = self.seats.get(old_pilot.vehicle_seat)

            if seat is not None:
                await seat.remove_player(old_pilot)

            # Check if the vehicle is now empty
            for seat in self.seats.values():
                if seat.player is not None:
                    self.team == Team.NONE
                    print("VEHICLE IS NOW EMPTY AND TEAMLESS")
                    return


    def get_player_seat(self, player_id: int):
        for seat_id, seat in self.seats.items():
            if seat.player_id == player_id:
                return seat_id
        return None

    async def switch_seat(self, player, target_seat_id: int) -> bool:
        async with self._vehicle_lock:
            # Find the current seat of the player
            current_seat_id = self.get_player_seat(player.id)
            if current_seat_id is None:
                # Player is not in any seat
                return False

            # Check if the target seat exists and is empty
            if target_seat_id not in self.seats:
                return False

            target_seat = self.seats[target_seat_id]
            current_seat = self.seats[current_seat_id]

            if not target_seat.can_seat():
                # Target seat is not empty
                return False

            # Remove player from the current seat
            await current_seat.remove_player(player)

            # Add player to the target seat
            success = await target_seat.add_player(player)
            if success:
                return True

            # Re-add player to the original seat if switching failed
            await current_seat.add_player(player)
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
            if self.player_id == player.id:
                self.player = None
                self.player_id = -1
