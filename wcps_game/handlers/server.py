import logging

from handlers.packet_handler import PacketHandler
from packets.internals import InternalPlayerAuthorization
from packets.server import ServerTime, LeaveServer, PlayerAuthorization, Ping

from wcps_core.constants import ErrorCodes

class RequestServerTimeHandler(PacketHandler):
    async def process(self, u) -> None:

        self._client_version = self.get_block(1)
        self._mac_address = self.get_block(2)

        ## this client ver is reported as 3
        ## TODO: can this be used for anything?

        if not self._client_version.isdigit() or not int(self._client_version) == 3:
            await u.send(ServerTime(ServerTime.ErrorCodes.DifferentClientVersion).build())
            await u.disconnect()
            return
        
        ##TODO: mac ban?
        if len(self._mac_address) !=12 or not self._mac_address.isalnum():
            await u.send(PlayerAuthorization(PlayerAuthorization.ErrorCodes.NotAccessible).build())
            await u.disconnect()
            return
        
        ## 24576 0
        await u.send(ServerTime(ErrorCodes.SUCCESS).build())


class LeaveServerHandler(PacketHandler):
    async def process(self, u) -> None:

        if u.authorized:
            ##TODO: Graceful disconnect tasks here? Maybe they are
            ## beter on the disconnect() call of the socket/servers
            await u.send(LeaveServer().build())
            await u.disconnect()
            logging.info("Player left the server")


## Instead of authorizing and moving on to the equipment packet,
## we will instead send an internal authentication packet to the auth
## and in that handler we will send the equipment packet if everything is ok
class ClientAuthentication(PacketHandler):
    async def process(self, u) -> None:
        #14167454 25088 1 -1 darkraptor DarkRaptor 0 0 910 1 -1 -1 -1 -1 0 1 1 dnjfhr^ 

        self._internal_id = self.get_block(0)
        self._username = self.get_block(2)
        self._displayname = self.get_block(3)
        ##TODO: Make sure these do not crash the server
        self._reported_client_session = int(self.get_block(4))
        self._reported_access_level = int(self.get_block(7))

        if self._reported_client_session not in range(-32767, 32768):
            await u.send(PlayerAuthorization(PlayerAuthorization.ErrorCodes.InvalidPacket).build())
            await u.disconnect()
            return
        
        ## Banned player?
        if self._reported_access_level <= 0:
            await u.send(PlayerAuthorization(PlayerAuthorization.ErrorCodes.NotAccessible).build())
            await u.disconnect()
            return

        ## Session exists already
        if await self.this_server.is_online(self._reported_client_session):
            await u.send(PlayerAuthorization(PlayerAuthorization.ErrorCodes.IdInUse).build())
            await u.disconnect()
            return

        if all(is_valid_length(name) for name in [self._username, self._displayname]):

            ## temporary set their username for keying, it will be checked again later
            u.username = self._username
            ## temporarily add users even if their data is incomplete, it will be
            ## reset on correct authorization
            await self.this_server.add_player(u)

            await self.this_auth.send(InternalPlayerAuthorization(
                error_code=ErrorCodes.SUCCESS, 
                session_id=self._reported_client_session,
                username=self._username,
                rights=self._reported_access_level
                ).build())
        else:
            await u.send(PlayerAuthorization(PlayerAuthorization.ErrorCodes.NicknameToShort).build())
            await u.disconnect()

class Ping(PacketHandler):
    async def process(self, u) -> None:
        if u.authorized:
            await u.answer_ping()
        else:
            u.disconnect()


def is_valid_length(value, min_length=3, max_length=12):
    return min_length <= len(value) <= max_length

