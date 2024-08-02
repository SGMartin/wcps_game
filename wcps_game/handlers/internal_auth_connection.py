from wcps_game.entities.game_server import GameServer
from wcps_game.handlers.packet_handler import PacketHandler
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory


class AuthConnectionHandler(PacketHandler):
    async def process(self, server: GameServer) -> None:
        details_packet = PacketFactory.create_packet(
            packet_id=PacketList.INTERNAL_GAME_AUTHENTICATION,
            server=None  # TODO
        )
        await server.send(details_packet.build())
