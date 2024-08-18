from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus, Classes


class BranchSelectHandler(GameProcessHandler):
    async def handle(self):
        if self.room.state != RoomStatus.PLAYING:
            return

        target_class = int(self.get_block(2))
        self.player.round_start()

        if target_class >= Classes.ENGINEER and target_class <= Classes.HEAVY:
            self.set_block(2, target_class)
            self.player.branch = target_class

        self.answer = True
