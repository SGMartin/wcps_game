from wcps_game.handlers.packet_handler import PacketHandler, register_handler
from wcps_game.packets.packet_list import PacketList

import wcps_core.packets

@register_handler(wcps_core.packets.PacketList.ClientConnection)
class SomeInternalHandler(PacketHandler):
    async def process(self, user: 'User') -> None:
        # Handler logic here
        print("HERE")
