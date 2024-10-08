import asyncio

from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.packets.packet_list import PacketList


class GameSetupHandler(GameProcessHandler):
    async def handle(self):

        self.sub_packet = PacketList.DO_GO
        self.set_block(2, 3)  # 100% sure this is the spawn protection time :)
        self.set_block(3, 500)  # Unknown
        self.set_block(4, 0)  # unknown
        self.set_block(5, 1)  # is this the team?

        # Each player in the room will trigger this handler
        # So do not create the room task twice
        if not self.room.running:
            self.room.running = True
            asyncio.create_task(self.room.run())

        # Request a mapData update here
        self.map_data = True
        self.self_target = True
        self.answer = True
