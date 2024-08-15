from wcps_game.handlers.packet_handler import GameProcessHandler

from wcps_game.game.constants import RoomStatus
from wcps_game.client.maps import MapDatabase


class ChangeMapHandler(GameProcessHandler):
    async def handle(self):
        if self.player.id != self.room.master_slot:  # This player is not the master
            # TODO: log this? Cheater?
            return

        if self.room.state != RoomStatus.WAITING:
            return

        new_map = self.get_block(2)
        this_room_mode = self.room.game_mode
        this_room_channel = self.room.channel.type

        # Is this a valid map?
        map_database = MapDatabase()
        # TODO: sanitize input
        self.room.current_map = new_map

        self.update_lobby = True
        self.answer = True
