from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import ChannelType, RoomStatus


class LeaveVehicleHandler(GameProcessHandler):
    async def handle(self):
        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.WAITING:
            return

        if self.room.channel.type not in [ChannelType.URBANOPS, ChannelType.BATTLEGROUP]:
            return

        # NOTE: this packet is also sent when you are killed in a vehicle (think AW50F)
        # SO do not return on player status

        if self.player.vehicle_id == -1 or self.player.vehicle_seat == -1:
            return

        requested_vehicle = int(self.get_block(2))
        main_weapon_current_ammo = int(self.get_block(4))
        main_weapon_current_magazine = int(self.get_block(5))
        sub_weapon_current_ammo = int(self.get_block(6))
        sub_weapon_current_magazine = int(self.get_block(7))

        target_vehicle = self.room.vehicles.get(requested_vehicle)

        if target_vehicle is None:
            print(f"Target vehicle {target_vehicle} does not exist")
            return

        this_seat = target_vehicle.seats.get(self.player.vehicle_seat)

        if this_seat is None:
            print(f"Error targeting vehicle seat {self.player.vehicle_seat}")
            return

        # Update weapons
        target_vehicle.seats[self.player.id].main_weapon_ammo = main_weapon_current_ammo
        target_vehicle.seats[self.player.id].sub_weapon_ammo = sub_weapon_current_ammo
        target_vehicle.seats[self.player.id].main_weapon_magazine = main_weapon_current_magazine
        target_vehicle.seats[self.player.id].sub_weapon_magazine = sub_weapon_current_magazine

        # Vacant seat
        await target_vehicle.leave_vehicle(self.player)
        self.player.leave_vehicle()

        self.set_block(2, target_vehicle.id)
        self.set_block(3, this_seat.id)
        self.set_block(4, main_weapon_current_ammo)
        self.set_block(5, main_weapon_current_magazine)
        self.set_block(6, sub_weapon_current_ammo)
        self.set_block(7, sub_weapon_current_magazine)
        self.set_block(8, 0)  # ??
        self.set_block(9, 0)  # ??

        self.answer = True
