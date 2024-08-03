import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import GameServer

from wcps_core.constants import ErrorCodes as er

from wcps_game.handlers.packet_handler import PacketHandler


class AuthorizeServerHandler(PacketHandler):
    async def process(self, server: "GameServer") -> None:
        error_code = int(self.get_block(0))

        error_messages = {
            er.SERVER_LIMIT_REACHED: "Max server capacity reached in authentication server",
            er.INVALID_SERVER_TYPE: "Invalid server type. Rejected by authentication server",
            er.INVALID_SESSION_MATCH: "Authentication server does not recognize game server",
            er.ALREADY_AUTHORIZED: "Server already registered",
            er.SERVER_ERROR_OTHER: "Unknown error. Check game server credentials"
        }

        if error_code in error_messages:
            logging.error(error_messages[error_code])
            await server.disconnect()
            return

        if error_code == er.SUCCESS:
            session_id = self.get_block(1)

            if server.is_first_authorized:
                server.authorize(session_id=session_id)
            else:
                logging.info("Game Server reconnected to authentication. Update?")
                # TODO: Update and sync routine
                server.authorize(session_id=session_id)
        else:
            logging.error(f"Unknown error {error_code}")
            await server.disconnect()
            return