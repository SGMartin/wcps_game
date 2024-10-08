import logging

from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus


class PlayerDamageHandler(GameProcessHandler):
    async def handle(self):
        if self.room.state == RoomStatus.PLAYING:
            if len(self.blocks) == 24:
                await self.room.current_game_mode.on_damage(self)
            else:
                logging.info(f"Incorrect damage packet length {len(self.blocks)}")
