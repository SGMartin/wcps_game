import logging

from wcps_game.client.items import ItemDatabase
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

        # p2: 0 heal, 1 drowning, 2 adrenaline (client 0x4e4860). 3 (stamina) is only sent by the server
        drowning_byte = int(self.get_block(4))

        if drowning_byte in (0, 2):
            should_heal = True
        elif drowning_byte == 1:
            should_heal = False
        else:
            return

        if not self.player.alive:
            return

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

        weapon_code = None
        if not is_healing_post:
            weapon_code = ItemDatabase().weapon_code(self.player.weapon)
            if weapon_code not in HealingPower.HEALING_POWER:
                logging.error(
                    f"{self.player.user.displayname} healed with weapon {self.player.weapon} "
                    f"({weapon_code}), which does not heal"
                )
                return

        # The server decides the target: adrenaline (an autoinjector) is self only, whatever the packet
        # says, and FFA has no teammates to heal
        if weapon_code == HealingPower.ADRENALINE or self.room.game_mode == GameMode.FFA:
            target = self.player
        else:
            if target not in range(0, self.room.max_players):
                return
            target = self.room.players[target]

        if target is None or not target.alive:
            return

        if target.health >= 1000:
            return

        if target.team != self.player.team:
            return

        if target != self.player:
            await self.player.add_assists(assists=1)  # it was never awaited: the assist was lost

        if is_healing_post:
            hp_to_heal = 400
        elif weapon_code == HealingPower.ADRENALINE and target.health < 400:
            hp_to_heal = 400 - target.health
        else:
            hp_to_heal = HealingPower.HEALING_POWER[weapon_code]

        target.health = target.health + hp_to_heal

        if target.health > 1000:
            target.health = 1000

        self.set_block(3, target.health)
        self.answer = True
