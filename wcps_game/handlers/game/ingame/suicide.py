from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus, GameMode, DeathCause
from wcps_game.packets.packet_list import PacketList


class SuicideHandler(GameProcessHandler):
    async def handle(self):

        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.WAITING:
            return

        if not self.player.alive:
            return

        # p1 = cause. The client sends 0 for the suicide key and 5 (mine message) when the danger zone
        # countdown runs out; it does not kill itself, it waits for this answer
        cause = int(self.get_block(3))
        if cause != DeathCause.MINE:
            cause = DeathCause.SUICIDE

        # No voluntary suicide in Explosive and FFA. The danger zone still kills there.
        if cause == DeathCause.SUICIDE and self.room.game_mode in (GameMode.EXPLOSIVE, GameMode.FFA):
            return

        self.sub_packet = PacketList.DO_SUICIDE

        await self.player.suicide()
        await self.room.current_game_mode.on_suicide(self.player)

        self.set_block(2, self.player.id)
        self.set_block(3, cause)
        self.answer = True
