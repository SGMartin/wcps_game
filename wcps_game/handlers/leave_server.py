from wcps_game.entities.user import User
from wcps_game.handlers.packet_handler import PacketHandler


class LeaveServerHandler(PacketHandler):
    async def process(self, u: User) -> None:
        if u.authorized:
            await u.leave_server()
