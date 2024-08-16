from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus


class ToggleAutoStartHandler(GameProcessHandler):
    async def handle(self):
        if self.player.id != self.room.master_slot:  # This player is not the master
            # TODO: log this? Cheater?
            return

        if self.room.state != RoomStatus.WAITING:
            return

        self.room.autostart = not self.room.autostart

        self.set_block(2, self.room.autostart)
        self.update_lobby = True
        self.answer = True
