from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus


class CaptureFlagHandler(GameProcessHandler):
    async def handle(self):

        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.WAITING:
            return

        if not self.player.alive:
            return

        if self.player.team is None:
            return

        captured_flag_id = int(self.get_block(2))

        # Fine even for conquest since we flush spawn_flags
        if captured_flag_id in self.room.spawn_flags.values():
            return

        old_flag_team = self.room.flags[captured_flag_id]

        if old_flag_team == -1:
            self.room.flags[captured_flag_id] = self.player.Team
        else:
            self.room.flags[captured_flag_id] = -1

        self.set_block(2, captured_flag_id)
        self.set_block(3, self.room.flags[captured_flag_id])
        self.answer = True

        # TODO: add flags captured and call OnFlagCaptured here
