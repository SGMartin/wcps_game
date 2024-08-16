import logging

from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.packets.packet_list import PacketList

from wcps_game.handlers.game.change_map import ChangeMapHandler
from wcps_game.handlers.game.change_mode import ChangeGameModeHandler

# Dictionary to map packet IDs to handler classes
HANDLER_MAP = {
    # Lobby subpackets
    PacketList.DO_MAP_CLICK: ChangeMapHandler,
    PacketList.DO_TYPE_CLICK: ChangeGameModeHandler
}


def get_subhandler_for_packet(subpacket_id: int) -> GameProcessHandler:
    handler_class = HANDLER_MAP.get(subpacket_id)
    if handler_class:
        return handler_class()
    else:
        logging.info(f"Unknown subpacket: {subpacket_id}")
        return None
