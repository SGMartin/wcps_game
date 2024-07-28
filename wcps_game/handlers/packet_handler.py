import abc
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from clients import AuthenticationClient
    from game.game_server import GameServer

import wcps_core.packets

class PacketHandler(abc.ABC):
    def __init__(self, this_server: "GameServer"):
        self.in_packet = None
        self.this_server = this_server

    async def handle(self, packet_to_handle: wcps_core.packets.InPacket) -> None:
        self.in_packet = packet_to_handle
        receptor = packet_to_handle.receptor

        # Local import to avoid circular dependency
        from clients import AuthenticationClient  
        
        if isinstance(receptor, AuthenticationClient):
            await self.process(receptor)
        else:
            logging.error("No receptor for this packet!")


    @abc.abstractmethod
    async def process(self, user_or_server):
        pass

    def get_block(self, block_id: int) -> str:
        return self.in_packet.blocks[block_id]