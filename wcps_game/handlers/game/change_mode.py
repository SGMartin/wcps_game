from wcps_game.handlers.packet_handler import GameProcessHandler

from wcps_game.game.constants import GameMode, RoomStatus
from wcps_game.client.maps import MapDatabase


class ChangeGameModeHandler(GameProcessHandler):
    async def handle(self):
        if self.player.id != self.room.master_slot:  # This player is not the master
            # TODO: log this? Cheater?
            return

        if self.room.state != RoomStatus.WAITING:
            return

        new_game_mode = int(self.get_block(2))

        if new_game_mode > 3:
            new_game_mode = 3

        if new_game_mode < 0:
            new_game_mode = 0

        self.room.game_mode = new_game_mode

        # Get the first map available for this mode
        map_database = MapDatabase()
        map_for_mode = map_database.get_first_map_for_mode(
            game_mode=new_game_mode,
            channel=self.room.channel.type
            )
        self.room.current_map = map_for_mode

        cqc_rounds = self.room.rounds_setting if self.room.game_mode == GameMode.EXPLOSIVE else 0
        tdm_tickets = self.room.tickets_setting if self.room.game_mode != GameMode.EXPLOSIVE else 0

        self.set_block(2, new_game_mode)
        self.set_block(3, self.room.current_map)
        self.set_block(4, cqc_rounds)
        self.set_block(5, tdm_tickets)

        self.update_lobby = True
        self.answer = True
