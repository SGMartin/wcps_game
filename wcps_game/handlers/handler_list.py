import logging

import wcps_core.packets

import handlers.internals
from handlers.packet_handler import PacketHandler

def get_handler_for_packet(packet_id: int) -> PacketHandler:
    if packet_id in handlers:
        ## return a new initialized instance of the handler
        return handlers[packet_id]()
    else:
        logging.info(f"Unknown packet ID {packet_id}")
        return None


handlers = {
    ## Internal packets ##
   wcps_core.packets.PacketList.ClientConnection: handlers.internals.AuthConnectionHandler
}