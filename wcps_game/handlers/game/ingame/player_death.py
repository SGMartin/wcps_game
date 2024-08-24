from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus

from wcps_game.packets.packet_list import PacketList


# Manual handler to call player death on specific cases
# The game does not send a death subpacket AFAIK
# That's why we do not check much
class PlayerDeathHandler(GameProcessHandler):
    async def handle(self):

        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.WAITING:
            return

        if not self.player.alive:
            return

        if self.player.team is None:
            return

        await self.player.add_deaths()

        self.sub_packet = PacketList.DO_PLAYER_DIE
        self.set_block(3, self.player.id)
        self.set_block(12, 0)
        self.set_block(13, self.player.health)

        self.answer = True
