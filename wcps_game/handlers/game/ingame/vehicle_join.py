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
            return self.reject()

        requested_vehicle = int(self.get_block(2))

        target_vehicle = self.room.vehicles.get(requested_vehicle)

        if target_vehicle is None:
            logging.error(f"Target vehicle {requested_vehicle} does not exist")
            return self.reject()

        joined = await target_vehicle.join_vehicle(new_pilot=self.player)

        if not joined:
            return self.reject()

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

    def reject(self):
        """The client sets a "boarding pending" flag when it asks (PF23 0x4c8549) and only clears it in the
        0xc8 handler (0x4e61b0); while it is set, the suicide key does nothing. Answer only the requester with
        p0 = -1: the handler clears the flag and stops at its p0 >= 0 check."""
        self.set_block(2, -1)
        self.self_target = True
        self.answer = True
