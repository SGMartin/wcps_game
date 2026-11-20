from wcps_game.handlers.packet_handler import GameProcessHandler

from wcps_game.game.constants import RoomStatus
from wcps_game.packets.error_codes import RoomKickError


class StartRoomHandler(GameProcessHandler):
    async def handle(self):
        if self.player.id != self.room.master_slot:  # This player is not the master
            # TODO: log this? Cheater?
            return

        # Already playing, WTF
        if self.room.state != RoomStatus.WAITING:
            return

        # Same rules as Auto Start (Room.can_start). Members-only maps: the client checks them before
        # sending this packet (s_MapIsMembershipOnly), so failing here gets no answer, as the other
        # invalid cases.
        if self.room.can_start():
            await self.room.launch()
        else:
            # m774 "Not enough players. Cannot start game." (client DO_GAME_PROCESS error table)
            self.error_code = RoomKickError.NOT_ENOUGH_PLAYERS
            self.answer = True
