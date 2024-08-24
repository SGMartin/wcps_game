from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus


class ConfirmDeathHandler(GameProcessHandler):
    async def handle(self):
        if self.room.state != RoomStatus.PLAYING:
            return

        # This subpacket is sent after every death related stuff has happened
        # So it's a very good place to reset vehicle stats for instance
        # Since we have not to worry about the client sending vehicle leave after the player
        # dies on a vehicle

        if not self.player.alive and self.player.health == 0:
            await self.player.reset_vehicle_status()
