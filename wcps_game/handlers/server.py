import logging

from handlers.packet_handler import PacketHandler
from packets.server import ServerTime, LeaveServer

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
            ##TODO: auth normal procedure here
            return
        
        ## 24576 0
        await u.send(ServerTime(ErrorCodes.SUCCESS).build())


class LeaveServerHandler(PacketHandler):
    async def process(self, u) -> None:

        if u.authorized:
            ##TODO: Graceful disconnect tasks here? Maybe they are
            ## beter on the disconnect() call of the socket/servers
            await u.send(LeaveServer().build())
            log.info("Player left the server")