from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus


class SpawnHandler(GameProcessHandler):
    async def handle(self):

        if self.room.state == RoomStatus.PLAYING and self.player.can_spawn:
            this_spawnslot = await self.room.current_game_mode.get_spawn_id()

            # Client 0x4e67b0: p4 and p5 are the player's kills and deaths, p6 the spawn point in FFA
            # (p0 otherwise). The client sends p3..p7 = 0; forwarding them reset the scoreboard K/D of the
            # player on every respawn (until the next DO_GAME_SCORE).
            self.set_block(6, self.player.kills)  # p4
            self.set_block(7, self.player.deaths)  # p5
            self.set_block(8, this_spawnslot)  # p6
            self.set_block(9, 0)  # p7, not read

            self.player.spawn(int(self.get_block(3)))
            self.answer = True
