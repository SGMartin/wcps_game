from handlers.packet_handler import PacketHandler

from packets.internals import GameServerDetails

class AuthConnectionHandler(PacketHandler):
    async def process(self, server) -> None:
        await server.send(GameServerDetails().build())
        