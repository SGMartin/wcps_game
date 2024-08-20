from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus


class AmmoRechargeHandler(GameProcessHandler):
    async def handle(self):

        if self.room.state == RoomStatus.WAITING:
            return

        if not self.player.alive:
            return

        self.answer = True
