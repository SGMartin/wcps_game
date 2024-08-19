from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_game.handlers.packet_handler import PacketHandler

from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.error_codes import PlayerAuthorizationError

# Instead of authorizing and moving on to the equipment packet,
# we will instead send an internal authentication packet to the auth
# and in that handler we will send the equipment packet if everything is ok


class ClientAuthenticationHandler(PacketHandler):
    async def process(self, u: "User") -> None:

        internal_id = self.get_block(0)
        username = self.get_block(2)
        displayname = self.get_block(3)
        # TODO: Make sure these do not crash the server
        reported_client_session = int(self.get_block(4))
        reported_access_level = int(self.get_block(7))

        if reported_client_session not in range(-32767, 32768):
            error_packet = PacketFactory.create_packet(
                packet_id=PacketList.PLAYER_AUTHORIZATION,
                error_code=PlayerAuthorizationError.INVALID_PACKET
                )
            await u.send(error_packet.build())
            await u.disconnect()
            return

        # Banned player?
        if reported_access_level <= 0:
            error_packet = PacketFactory.create_packet(
                packet_id=PacketList.PLAYER_AUTHORIZATION,
                error_code=PlayerAuthorizationError.NOT_ACCESIBLE
                )
            await u.send(error_packet.build())
            await u.disconnect()
            return

        # Session exists already
        if await u.this_server.is_online(reported_client_session):
            error_packet = PacketFactory.create_packet(
                packet_id=PacketList.PLAYER_AUTHORIZATION,
                error_code=PlayerAuthorizationError.IDIN_USE
                )
            await u.send(error_packet.build())
            await u.disconnect()
            return

        # Server reached maximum capacity
        if u.this_server.get_player_count() >= u.this_server.max_players:
            error_packet = PacketFactory.create_packet(
                packet_id=PacketList.PLAYER_AUTHORIZATION,
                error_code=PlayerAuthorizationError.SERVER_FULL
            )
            await u.send(error_packet.build())
            await u.disconnect()
            return

        if all(is_valid_length(name) for name in [username, displayname]):

            # temporary set their username for keying, it will be checked again later
            u.internal_id = int(internal_id)  # legacy, but included for now for testing
            u.username = username
            u.displayname = displayname
            # temporarily add users even if their data is incomplete, it will be
            # reset on correct authorization
            await u.this_server.add_player(u)

            internal_auth_packet = PacketFactory.create_packet(
                PacketList.INTERNAL_PLAYER_AUTHENTICATION,
                error_code=1,
                session_id=reported_client_session,
                username=username,
                rights=reported_access_level
            )
            await u.this_server.send(internal_auth_packet.build())
        else:
            error_packet = PacketFactory.create_packet(
                packet_id=PacketList.PLAYER_AUTHORIZATION,
                error_code=PlayerAuthorizationError.NICKNAME_TOO_SHORT
                )
            await u.send(error_packet.build())
            await u.disconnect()


def is_valid_length(value, min_length=3, max_length=12):
    return min_length <= len(value) <= max_length
