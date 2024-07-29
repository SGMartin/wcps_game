import logging
from typing import TYPE_CHECKING

import wcps_core.packets

from handlers.packet_handler import PacketHandler
from packets.server import PacketList as sp

if TYPE_CHECKING:
    from game.game_server import GameServer
    from clients import AuthenticationClient
    import handlers.internals
    import handlers.server

def get_handler_for_packet(packet_id: int, game_server: 'GameServer', auth_client: "AuthenticationClient") -> 'PacketHandler':

    ## Ugly anticircular imports
    import handlers.internals
    import handlers.server

    handlers = {
    ## Internal packets ##
   wcps_core.packets.PacketList.ClientConnection: handlers.internals.AuthConnectionHandler,
   wcps_core.packets.PacketList.GameServerAuthentication: handlers.internals.AuthorizeServerHandler,

    ## Lobby / main packets ##
    sp.ServerTime: handlers.server.RequestServerTimeHandler,
    sp.LeaveServer: handlers.server.LeaveServer,
    sp.Authorization: handlers.server.ClientAuthentication
}


    if packet_id in handlers:
        ## return a new initialized instance of the handler
        return handlers[packet_id](game_server, auth_client)
    else:
        logging.info(f"Unknown packet ID {packet_id}")
        return None