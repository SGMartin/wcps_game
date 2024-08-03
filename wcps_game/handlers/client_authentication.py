from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_game.handlers.packet_handler import PacketHandler

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
            await u.send(PlayerAuthorization(PlayerAuthorization.ErrorCodes.InvalidPacket).build())
            await u.disconnect()
            return
        
        # Banned player?
        if reported_access_level <= 0:
            await u.send(PlayerAuthorization(PlayerAuthorization.ErrorCodes.NotAccessible).build())
            await u.disconnect()
            return

        # Session exists already
        if await self.this_server.is_online(reported_client_session):
            await u.send(PlayerAuthorization(PlayerAuthorization.ErrorCodes.IdInUse).build())
            await u.disconnect()
            return

        if all(is_valid_length(name) for name in [username, displayname]):

            # temporary set their username for keying, it will be checked again later
            u.username = username
            # temporarily add users even if their data is incomplete, it will be
            # reset on correct authorization
            await self.this_server.add_player(u)

            await self.this_auth.send(InternalPlayerAuthorization(
                error_code=ErrorCodes.SUCCESS,
                session_id=reported_client_session,
                username=username,
                rights=reported_access_level
                ).build())
        else:
            await u.send(PlayerAuthorization(PlayerAuthorization.ErrorCodes.NicknameToShort).build())
            await u.disconnect()


def is_valid_length(value, min_length=3, max_length=12):
    return min_length <= len(value) <= max_length