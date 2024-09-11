from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import GameMode, RoomStatus


class ConfirmRoundStart(GameProcessHandler):
    async def handle(self):

        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.WAITING:
            return

        if self.room.game_mode != GameMode.EXPLOSIVE:
            return

        self.player.round_start()
