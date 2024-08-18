from wcps_game.handlers.packet_handler import GameProcessHandler

from wcps_game.game.constants import RoomStatus, ROUND_LIMITS, ChannelType, GameMode


class ChangeRoundsHandler(GameProcessHandler):
    async def handle(self):
        if self.player.id != self.room.master_slot:  # This player is not the master
            # TODO: log this? Cheater?
            return

        if self.room.state != RoomStatus.WAITING:
            return

        if self.room.channel.type != ChannelType.CQC:
            return

        if self.room.game_mode != GameMode.EXPLOSIVE:
            return

        target_rounds = int(self.get_block(2))

        if target_rounds not in range(0, len(ROUND_LIMITS)):
            target_rounds = 0

        self.room.update_rounds_from_settings(
            settings=target_rounds
            )
        self.set_block(2, self.room.rounds_setting)

        self.update_lobby = True
        self.answer = True
