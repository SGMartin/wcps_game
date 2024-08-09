from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User


from wcps_core.constants import ErrorCodes as corerr

from wcps_game.handlers.packet_handler import PacketHandler

from wcps_game.packets.error_codes import ServerTimeError, PlayerAuthorizationError
from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.packet_list import PacketList


class RequestServerTimeHandler(PacketHandler):
    async def process(self, u: "User") -> None:
        # this client version is reported as 3
        # TODO: can this be used for anything?

        client_version = self.get_block(1)
        mac_address = self.get_block(2)

        if not client_version.isdigit() or not int(client_version) == 3:
            packet = PacketFactory.create_packet(
                packet_id=PacketList.REQUEST_SERVER_TIME,
                error_code=ServerTimeError.CLIENT_VERSION_MISSMATCH
                )
            await u.send(packet.build())
            await u.disconnect()
            return

        # TODO: mac ban?
        if len(mac_address) != 12 or not mac_address.isalnum():
            packet = PacketFactory.create_packet(
                packet_id=PacketList.PLAYER_AUTHORIZATION,
                error_code=PlayerAuthorizationError.NOT_ACCESIBLE
                )
            await u.send(packet.build())
            await u.disconnect()
            return

        success_packet = PacketFactory.create_packet(
            packet_id=PacketList.REQUEST_SERVER_TIME,
            error_code=corerr.SUCCESS
        )

        await u.send(success_packet.build())
