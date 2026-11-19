from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus


class ToggleAutoStartHandler(GameProcessHandler):
    async def handle(self):
        if self.player.id != self.room.master_slot:  # This player is not the master
            # TODO: log this? Cheater?
            return

        if self.room.state != RoomStatus.WAITING:
            return

        # p0 is the value the client asks for (a toggle could desync and do the opposite). The map
        # selector also sends 0 when the master's premium does not allow Auto Start on the new map.
        self.room.autostart = bool(int(self.get_block(2)))

        self.set_block(2, self.room.autostart)
        self.update_lobby = True
        self.answer = True
        await self.room.check_autostart()
