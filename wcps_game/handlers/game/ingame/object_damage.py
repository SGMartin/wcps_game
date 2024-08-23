from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus


class ObjectDamageHandler(GameProcessHandler):
    async def handle(self):
        if self.room.state == RoomStatus.PLAYING:
            if len(self.blocks) == 24:
                await self.room.current_game_mode.on_object_damage(self)
            else:
                print("WTF OBJECT LENGTH PACKET")
                print(len(self.blocks))
