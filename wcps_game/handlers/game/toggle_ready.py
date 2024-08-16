from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus


class ToggleReadyHandler(GameProcessHandler):
    async def handle(self):

        if self.room.state != RoomStatus.WAITING:
            return

        # Masters do not toggle ready
        if self.player.id == self.room.master_slot:
            return

        self.player.toggle_ready()
        self.set_block(2, self.player.ready)

        self.answer = True
