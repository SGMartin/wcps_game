from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus, GameMode
from wcps_game.packets.packet_list import PacketList


class SuicideHandler(GameProcessHandler):
    async def handle(self):

        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.WAITING:
            return

        if not self.player.alive:
            return

        if self.room.game_mode == GameMode.EXPLOSIVE or self.room.game_mode == GameMode.FFA:
            return

        self.sub_packet = PacketList.DO_SUICIDE

        await self.player.suicide()
        await self.room.current_game_mode.on_suicide(self.player)

        self.set_block(2, self.player.id)
        self.set_block(3, 0)
        self.answer = True
