from wcps_game.entities.user import User
from wcps_game.handlers.packet_handler import PacketHandler


class PingHandler(PacketHandler):
    async def process(self, u: User) -> None:
        if u.authorized:
            await u.answer_ping()
        else:
            u.disconnect()
