import logging

from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import ChannelType, RoomStatus


class SwitchVehicleSeatHandler(GameProcessHandler):
    async def handle(self):
        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.WAITING:
            return

        if self.room.channel.type not in [ChannelType.URBANOPS, ChannelType.BATTLEGROUP]:
            return

        if not self.player.alive or self.player.vehicle_id == -1 or self.player.vehicle_seat == -1:
            return

        requested_vehicle = int(self.get_block(2))
        requested_vehicle_seat = int(self.get_block(3))
        main_weapon_current_ammo = int(self.get_block(4))
        main_weapon_current_magazine = int(self.get_block(5))
        sub_weapon_current_ammo = int(self.get_block(6))
        sub_weapon_current_magazine = int(self.get_block(7))

        target_vehicle = self.room.vehicles.get(requested_vehicle)

        if target_vehicle is None:
            logging.error(f"Target vehicle {target_vehicle} does not exist")
            return

        target_seat = target_vehicle.seats.get(requested_vehicle_seat)

        if target_seat is None:
            return

        can_switch = await target_vehicle.switch_seat(
            player=self.player,
            target_seat_id=requested_vehicle_seat
            )

        if not can_switch:
            return

        old_seat = self.player.vehicle_seat
        self.player.enter_vehicle(target_vehicle.id, requested_vehicle_seat)

        # Update ammo values for the old slot
        target_vehicle.seats[old_seat].main_weapon_ammo = main_weapon_current_ammo
        target_vehicle.seats[old_seat].main_weapon_magazine = main_weapon_current_magazine
        target_vehicle.seats[old_seat].sub_weapon_ammo = sub_weapon_current_ammo
        target_vehicle.seats[old_seat].sub_weapon_magazine = sub_weapon_current_magazine

        self.set_block(2, target_vehicle.id)
        self.set_block(3, requested_vehicle_seat)
        self.set_block(4, old_seat)
        self.set_block(5, target_vehicle.seats[requested_vehicle_seat].main_weapon_ammo)
        self.set_block(6, target_vehicle.seats[requested_vehicle_seat].main_weapon_magazine)
        self.set_block(7, target_vehicle.seats[requested_vehicle_seat].sub_weapon_ammo)
        self.set_block(8, target_vehicle.seats[requested_vehicle_seat].sub_weapon_magazine)

        self.answer = True
