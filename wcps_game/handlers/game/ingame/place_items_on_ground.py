from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus


class PlaceGroundItemHandler(GameProcessHandler):
    async def handle(self):

        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.WAITING:
            return

        if not self.player.alive:
            return

        item = self.get_block(22)

        if not self.player.user.inventory.has_item(item):
            return

        if self.player.items_planted >= 7:
            return

        self.room.add_item(owner=self.player, code=item)
        self.player.items_planted += 1
        self.set_block(4, len(self.room.ground_items))
        self.answer = True
