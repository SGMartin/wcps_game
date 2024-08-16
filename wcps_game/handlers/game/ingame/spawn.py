from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus


class SpawnHandler(GameProcessHandler):
    async def handle(self):

        if self.room.state == RoomStatus.PLAYING and self.player.can_spawn:
            self.set_block(7, 1)  # spawn slot
            self.set_block(8, 1)  # spawn slot
            self.set_block(9, 1)  # spawn slot

            self.player.spawn(int(self.get_block(3)))
            self.answer = True
