from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import Classes, ChannelType, RoomStatus


class CallArtilleryHandler(GameProcessHandler):
    async def handle(self):
        if not self.player.user.authorized:
            return

        if self.room.state != RoomStatus.PLAYING:
            return

        if self.room.channel.type != ChannelType.BATTLEGROUP:
            return

        if not self.player.alive:
            return

        if not self.player.branch == Classes.SNIPER:
            return

        # You need the binoculars for this
        if not self.player.user.inventory.has_item("DX01"):
            return

        self.set_block(3, 1)
        self.answer = True
