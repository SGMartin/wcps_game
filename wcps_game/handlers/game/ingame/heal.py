from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import GameMode, HealingPower, RoomStatus
from wcps_game.packets.packet_list import PacketList


class HealPlayerHandler(GameProcessHandler):
    async def handle(self):

        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.WAITING:
            return

        target = int(self.get_block(2))
        is_healing_post = bool(int(self.get_block(3)))

        # Drowning sends an empty heal subpacket with this byte set to 1
        drowning_byte = int(self.get_block(4))

        if drowning_byte == 0 or drowning_byte == 2:
            should_heal = True
        else:
            should_heal = False

        # Let's handle drowning first :)
        if not should_heal:
            self.player.health -= 100

            if self.player.health <= 0:

                await self.player.suicide()
                await self.room.current_game_mode.on_suicide(self.player)

                self.sub_packet = PacketList.DO_SUICIDE
                self.set_block(2, self.player.id)
                self.set_block(3, 0)
                self.answer = True

            else:
                self.set_block(3, self.player.health)
                self.answer = True

            return

        hp_to_heal = 0

        if target not in range(0, self.room.max_players):
            return

        target = self.room.players[target]

        if target is None:
            return

        if target.health >= 1000:
            return

        if target.team != self.player.team:
            return

        if self.room.game_mode == GameMode.FFA:
            target = self.player

        if target != self.player:
            self.player.add_assists(assists=1)

        if is_healing_post:
            hp_to_heal += 400
        else:
            if self.player.weapon == 65 and self.player.health < 400:  # adrenaline special shit
                hp_to_heal = 400 - self.player.health
            else:
                hp_to_heal = HealingPower.HEALING_POWER[self.player.weapon]

        target.health = target.health + hp_to_heal

        if target.health > 1000:
            target.health = 1000

        self.set_block(3, target.health)
        self.answer = True
