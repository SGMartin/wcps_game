from wcps_game.handlers.packet_handler import GameProcessHandler

from wcps_game.game.constants import RoomStatus
from wcps_game.packets.packet_list import PacketList


class StartRoomHandler(GameProcessHandler):
    async def handle(self):
        if self.player.id != self.room.master_slot:  # This player is not the master
            # TODO: log this? Cheater?
            return

        if self.room.state != RoomStatus.WAITING:
            return

        #  This is just a stub to get the handler ready in the branch
        #  Complete it when actual game modes are ready

        self.room.state = RoomStatus.PLAYING
        self.sub_packet = PacketList.DO_ROOM_START_CONFIRM
        self.set_block(2, self.room.current_map)
        self.answer = True
        self.update_lobby = True
