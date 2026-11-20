from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus, Classes


class BranchSelectHandler(GameProcessHandler):
    async def handle(self):
        if self.room.state != RoomStatus.PLAYING:
            return

        target_class = int(self.get_block(2))

        # Only the five classes. An invalid one used to be answered anyway, and every client stored it
        if target_class < Classes.ENGINEER or target_class > Classes.HEAVY:
            return

        # round_start() also allows the next spawn (can_spawn): a player who joins a running game only
        # gets it here, so it stays unconditional
        self.player.round_start()

        self.set_block(2, target_class)
        self.player.branch = target_class
        self.answer = True
