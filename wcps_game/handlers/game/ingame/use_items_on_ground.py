from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus


class UseGroundItemHandler(GameProcessHandler):
    async def handle(self):

        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.WAITING:
            return

        if not self.player.alive:
            return

        item_id = int(self.get_block(4))
        # item_code = self.get_block(22)  # We don't need it anymore since we stored it

        this_item = self.room.ground_items.get(item_id)
        if this_item is None:
            return

        success = await self.room.ground_items[item_id].activate()

        if not success:  # Possible concurrent access or lag. Do nothing
            return

        self_target = self.player == this_item.owner
        self_team = self.player.team == this_item.owner.team

        # No FF for flash or land but it should be possible lol >)
        if (self_target or self_team) and this_item.code in ["DU02", "DS05"]:
            return

        if this_item.code == "DU01" and not self_target and self_team:
            this_item.owner.add_assists(assists=3)

        if this_item.code == "DU02":  # land mine M14
            if self.player.health >= 500:
                self.player.health -= 300
            else:
                self.player.health = 200  # Land mines cannot kill you

            this_item.owner.add_assists(assists=5)

        if this_item.code == "DV01":  # Medic box
            self.player.health += 400

            if self.player.health >= 1000:
                self.player.health = 1000

            if not self_target and self_team:
                this_item.owner.add_assists(assists=3)

        print("ANSWERED")
        self.set_block(6, self.player.health)
        self.answer = True
