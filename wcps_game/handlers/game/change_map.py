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

        new_map = int(self.get_block(2))
        this_room_mode = self.room.game_mode
        this_room_channel = self.room.channel.type

        # Is this a valid map?
        map_database = MapDatabase()

        is_active = map_database.get_map_status(map_id=new_map)
        available_channels = map_database.get_map_channels(map_id=new_map)
        available_modes = map_database.get_map_modes(map_id=new_map)

        # Map inactive or not available for this channel
        # TODO: some of this stuff may be cheating. Log it
        if not is_active or not available_channels[this_room_channel]:
            print("Inactive map")
            return

        # Map mode is invalid
        if not available_modes[this_room_mode]:
            print("Invalid game mode")
            return

        self.room.current_map = new_map

        self.update_lobby = True
        self.answer = True
