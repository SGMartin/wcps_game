from wcps_game.game.constants import RoomStatus
from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.packets.packet_list import PacketList


class CollisionDamageHandler(GameProcessHandler):
    async def handle(self):

        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.WAITING:
            return

        is_player = bool(int(self.get_block(2)))  # 0 for vehicles. TODO
        # target_vehicle = int(self.get_block(4))
        damage_sustained = int(self.get_block(5))
        # out_of_playable_zone = int(self.get_block(6)) # TODO what are you doing soldier!

        if damage_sustained <= 0:
            return

        if not is_player:
            # TODO: vehicles
            return
        else:
            if not self.player.alive:
                return

            self.player.health -= damage_sustained

            # The player is killed because of the fall. Oddly, the game sends a suicide subpacket
            if self.player.health < 0:
                self.player.health = 0
                await self.player.add_deaths()
                await self.room.current_game_mode.on_player_suicide(player=self.player)

                self.set_block(2, self.player.id)
                self.sub_packet = PacketList.DO_SUICIDE

            self.set_block(7, damage_sustained)
            self.set_block(8, self.player.health)
            self.answer = True
