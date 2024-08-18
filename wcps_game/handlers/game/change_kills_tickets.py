from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus, ChannelType, GameMode


class ChangeKillsTicketsHandler(GameProcessHandler):
    async def handle(self):
        if self.player.id != self.room.master_slot:  # This player is not the master
            # TODO: log this? Cheater?
            return

        if self.room.state != RoomStatus.WAITING:
            return

        if self.room.game_mode not in [GameMode.FFA, GameMode.TDM]:
            return

        target_tickets = int(self.get_block(2))

        if self.room.channel.type == ChannelType.CQC:
            max_tickets = 4
        else:
            max_tickets = 5

        if target_tickets > max_tickets:
            target_tickets = 0

        self.room.update_tickets_from_settings(
            settings=target_tickets
        )

        self.set_block(2, target_tickets)
        self.update_lobby = True
        self.answer = True
