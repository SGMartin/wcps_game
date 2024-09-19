from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User


from wcps_game.handlers.packet_handler import PacketHandler
# from wcps_game.packets.packet_factory import PacketFactory
# from wcps_game.packets.packet_list import PacketList

# from wcps_core.constants import ErrorCodes as CoreErrors


class LeaveServerHandler(PacketHandler):
    async def process(self, u: "User") -> None:
        if u.authorized:
            pass
            # I moved everything to the User disconnect logic to handle both controlled and
            # uncontrolled (crashes) client leave requests
            # internal_leave = PacketFactory.create_packet(
            #     packet_id=PacketList.INTERNAL_PLAYER_AUTHENTICATION,
            #     error_code=CoreErrors.END_CONNECTION,
            #     session_id=u.session_id,
            #     username=u.username,
            #     rights=u.rights
            # )
            # await u.this_server.send(internal_leave.build())
