from wcps_game.handlers.packet_handler import GameProcessHandler

from wcps_game.game.constants import RoomStatus, Team, GameMode
from wcps_game.packets.packet_list import PacketList


class StartRoomHandler(GameProcessHandler):
    async def handle(self):
        if self.player.id != self.room.master_slot:  # This player is not the master
            # TODO: log this? Cheater?
            return

        # Already playing, WTF
        if self.room.state != RoomStatus.WAITING:
            return

        # This user is not the master
        if self.player.id != self.room.master_slot:
            return

        ready_derbaran = self.room.get_ready_player_count_in_team(Team.DERBARAN)
        ready_niu = self.room.get_ready_player_count_in_team(Team.NIU)

        can_start = False
        if self.room.game_mode == GameMode.FFA:
            if ready_derbaran + ready_niu > 1 or self.player.user.rights >= 3:
                can_start = True
        else:
            if ready_derbaran > 0 and ready_niu > 0:
                if abs(ready_derbaran - ready_niu) <= 2:  # TODO: make this configurable
                    can_start = True

            # Override settings because of admin rights
            if self.player.user.rights >= 3:
                can_start = True

        if can_start:
            self.room.state = RoomStatus.PLAYING
            self.sub_packet = PacketList.DO_ROOM_START_CONFIRM
            self.set_block(2, self.room.current_map)
            self.answer = True
            self.update_lobby = True
