import abc
import logging
from typing import Type, Dict, TYPE_CHECKING
from wcps_game.packets.packet_list import PacketList

if TYPE_CHECKING:
    from wcps_game.clients import AuthenticationClient
    from wcps_core.packets import InPacket

class PacketHandler(abc.ABC):
    def __init__(self):
        self.in_packet = None

    async def handle(self, packet_to_handle: 'InPacket') -> None:
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

# Registry to map packet IDs to handler classes
handler_mapping: Dict[int, Type[PacketHandler]] = {}

def register_handler(packet_id: int):
    def decorator(handler_class: Type[PacketHandler]):
        handler_mapping[packet_id] = handler_class
        return handler_class
    return decorator

def get_handler_for_packet(packet_id: int) -> Type[PacketHandler]:
    return handler_mapping.get(packet_id, None)()