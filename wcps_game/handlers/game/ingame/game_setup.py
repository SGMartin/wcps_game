from wcps_game.game.constants import RoomStatus
from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.packets.packet_list import PacketList


class GameSetupHandler(GameProcessHandler):
    async def handle(self):
        # A client still loading the map can send this after the game has ended. Answering it then
        # used to leave the room loop flag stuck, so the next game had no loop (#40). Ignored, as the
        # 2018 C# server did (Setup.cs: only while Playing).
        if self.room.state != RoomStatus.PLAYING:
            return

        self.sub_packet = PacketList.DO_GO
        self.set_block(2, 3)  # 100% sure this is the spawn protection time :)
        self.set_block(3, 500)  # Unknown
        self.set_block(4, 0)  # unknown
        self.set_block(5, 1)  # is this the team?

        # Each player in the room triggers this handler: the first one starts the room loop
        self.room.start_loop()

        # Request a mapData update here
        self.map_data = True
        self.self_target = True
        self.answer = True
