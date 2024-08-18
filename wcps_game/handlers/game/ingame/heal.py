from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import GameMode, HealingPower, RoomStatus


class HealPlayerHandler(GameProcessHandler):
    async def handle(self):

        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.WAITING:
            return

        target = int(self.get_block(2))
        is_healing_post = bool(int(self.get_block(3)))
        # should_heal = bool(int(self.get_block(5)))  # TODO: investigate this
        hp_to_heal = 0

        if target not in range(0, self.room.max_players):
            return

        target = self.room.players[target]

        if target is None:
            return

        if target.health >= 1000:
            return

        if target.team != self.player.team:
            if self.room.game_mode == GameMode.FFA:
                target = self.player
            else:
                return

        if target != self.player:
            self.player.add_assists(assists=1)

        if is_healing_post:
            hp_to_heal += 400
        else:
            if self.player.weapon == 82 and self.player.health < 400:  # adrenaline special shit
                hp_to_heal = 400 - self.player.health
            else:
                hp_to_heal = HealingPower.HEALING_POWER[self.player.weapon]

        target.health = target.health + hp_to_heal

        self.set_block(3, target.health)
        self.answer = True
