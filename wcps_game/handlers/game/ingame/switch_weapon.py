from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus


class SwitchWeaponHandler(GameProcessHandler):
    async def handle(self): 
        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.PLAYING:
            self.player.weapon = int(self.get_block(2))
            self.answer = True
