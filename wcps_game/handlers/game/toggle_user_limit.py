from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus


class ToggleUserLimitHandler(GameProcessHandler):
    async def handle(self):
        if self.player.id != self.room.master_slot:  # This player is not the master
            # TODO: log this? Cheater?
            return

        if self.room.state != RoomStatus.WAITING:
            return

        self.room.user_limit = not self.room.user_limit

        self.set_block(2, self.room.user_limit)
        self.update_lobby = True
        self.answer = True
