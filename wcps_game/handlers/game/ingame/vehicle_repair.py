import logging

from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import ChannelType, RoomStatus, Team


class RepairVehicleHandler(GameProcessHandler):
    async def handle(self):
        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.WAITING:
            return

        if self.room.channel.type not in [
            ChannelType.URBANOPS,
            ChannelType.BATTLEGROUP,
        ]:
            return

        if not self.player.alive:
            return

        target_vehicle = int(self.get_block(2))
        is_healing_station = bool(int(self.get_block(3)))
        target_vehicle = self.room.vehicles.get(target_vehicle)

        if target_vehicle is None:
            return

        if target_vehicle != Team.NONE and target_vehicle.team != self.player.team:
            return

        if target_vehicle.health >= target_vehicle.max_health:
            return

        if is_healing_station:
            repair_rate = 0.20
        else:
            # Get weapon codes. # TODO: careful here if these ids change down the line PF23
            if self.player.weapon == 63:  # default
                repair_rate = 0.10
            elif self.player.weapon == 64:  # pipe wrench
                repair_rate = 0.15
            else:
                repair_rate = 0
                logging.error(f"Failure to get repair rate for item {self.player.weapon}")

        if repair_rate > 0:
            health_gained = round(target_vehicle.max_health * repair_rate)
            target_vehicle.health += health_gained

            if target_vehicle.health > target_vehicle.max_health:
                target_vehicle.health = target_vehicle.max_health

            self.set_block(3, target_vehicle.health)
            self.set_block(4, target_vehicle.max_health)
            self.answer = True
