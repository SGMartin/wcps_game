from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus


class SpawnHandler(GameProcessHandler):
    async def handle(self):

        if self.room.state == RoomStatus.PLAYING and self.player.can_spawn:
            this_spawnslot = await self.room.current_game_mode.get_spawn_id()

            self.set_block(7, this_spawnslot)  # spawn slot
            self.set_block(8, this_spawnslot)  # spawn slot
            self.set_block(9, this_spawnslot)  # spawn slot

            self.player.spawn(int(self.get_block(3)))
            self.answer = True
