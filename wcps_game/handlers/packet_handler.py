import abc
from typing import Type, Dict

import wcps_core.packets

class PacketHandler(abc.ABC):
    def __init__(self):
        self.in_packet = None

    async def handle(self, packet_to_handle: wcps_core.packets.InPacket) -> None:
        self.in_packet = packet_to_handle
        receptor = packet_to_handle.receptor

        if isinstance(receptor, AuthenticationClient):
            await self.process(receptor)
        else:
            logging.error("No receptor for this packet!")

    @abc.abstractmethod
    async def process(self, user_or_server):
        pass

    def get_block(self, block_id: int) -> str:
        return self.in_packet.blocks[block_id]


handlers: Dict[int, Type[PacketHandler]] = {}

def register_handler(packet_id: int):
    def decorator(handler_class: Type[PacketHandler]):
        handlers[packet_id] = handler_class
        return handler_class
    return decorator

def get_handler_for_packet(packet_id: int) -> Type[PacketHandler]:
    return handlers.get(packet_id, None)()