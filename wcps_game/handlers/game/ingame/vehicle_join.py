import logging

from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import ChannelType, RoomStatus


class JoinVehicleHandler(GameProcessHandler):
    async def handle(self):
        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.WAITING:
            return

        if self.room.channel.type not in [ChannelType.URBANOPS, ChannelType.BATTLEGROUP]:
            return

        if not self.player.alive or self.player.vehicle_id != -1:
            return

        requested_vehicle = int(self.get_block(2))

        target_vehicle = self.room.vehicles.get(requested_vehicle)

        if target_vehicle is None:
            logging.error(f"Target vehicle {target_vehicle} does not exist")
            return

        joined = await target_vehicle.join_vehicle(new_pilot=self.player)

        if not joined:
            return

        new_seat_id = target_vehicle.get_player_seat(player_id=self.player.id)

        self.player.enter_vehicle(vehicle_id=target_vehicle.id, seat_id=new_seat_id)

        self.set_block(2, target_vehicle.id)
        self.set_block(3, new_seat_id)
        self.set_block(4, target_vehicle.health)
        self.set_block(5, target_vehicle.max_health)
        self.set_block(6, target_vehicle.seats[new_seat_id].main_weapon_ammo)
        self.set_block(7, target_vehicle.seats[new_seat_id].main_weapon_magazine)
        self.set_block(8, target_vehicle.seats[new_seat_id].sub_weapon_ammo)
        self.set_block(9, target_vehicle.seats[new_seat_id].sub_weapon_magazine)

        self.answer = True
