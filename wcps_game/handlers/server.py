import logging

from handlers.packet_handler import PacketHandler
from packets.server import ServerTime

from wcps_core.constants import ErrorCodes

class RequestServerTimeHandler(PacketHandler):
    async def process(self, u) -> None:

        self._client_version = self.get_block(1)
        self._mac_address = self.get_block(2)

        ## this client ver is reported as 3
        ## TODO: can this be used for anything?

        if self._client_version != 3:
            await u.send(ServerTime(ServerTime.ErrorCodes.DifferentClientVersion).build())
            await u.disconnect()
            return
        
        ##TODO: mac ban?
        if len(self._mac_address) !=12 or not self._mac_address.isalnum():
            ##TODO: auth normal procedure here
            return
        
        u.send(ServerTime(ErrorCodes.SUCCESS).build())
        
            