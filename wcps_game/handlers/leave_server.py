from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User


from wcps_game.handlers.packet_handler import PacketHandler


class LeaveServerHandler(PacketHandler):
    async def process(self, u: "User") -> None:
        if u.authorized:
            await u.leave_server()
