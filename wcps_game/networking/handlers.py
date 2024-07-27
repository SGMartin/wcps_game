import abc
import asyncio
import hashlib

from wcps_core.packets import InPacket
from wcps_core.constants import ErrorCodes
from wcps_core.constants import ServerTypes

import networking.packets

class PacketHandler(abc.ABC):
    def __init__(self):
        self.in_packet = None

    async def handle(self, packet_to_handle: InPacket) -> None:
        self.in_packet = packet_to_handle
        receptor = packet_to_handle.receptor

        if isinstance(receptor, AuthenticationClient) or isinstance(
            receptor, AuthenticationClient
        ):
            await self.process(receptor)
        else:
            print("No receptor for this packet!")

    @abc.abstractmethod
    async def process(self, user_or_server):
        pass

    def get_block(self, block_id: int) -> str:
        return self.in_packet.blocks[block_id]


def get_handler_for_packet(packet_id: int) -> PacketHandler:
    if packet_id in handlers:
        ## return a new initialized instance of the handler
        return handlers[packet_id]()
    else:
        print(f"Unknown packet ID {packet_id}")
        return None


handlers = {}
