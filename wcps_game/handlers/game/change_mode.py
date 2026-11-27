from wcps_game.handlers.packet_handler import GameProcessHandler

from wcps_game.config import settings
from wcps_game.game.constants import ChannelType, GameMode, RoomStatus, room_time_limit_index
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

        # CQC team deathmatch is 4 vs 4: only in 8 player rooms. A room's size cannot change once it is
        # created and CQC rooms start in Explosive, so this is the only way in
        if (
            new_game_mode == GameMode.TDM
            and self.room.channel.type == ChannelType.CQC
            and self.room.max_players > 8
        ):
            return

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
        # p4: time limit index. Left at 0 it reset the room time to 1 minute on every client
        self.set_block(6, room_time_limit_index(settings().game_time_limit))

        self.update_lobby = True
        self.answer = True
        await self.room.check_autostart()
