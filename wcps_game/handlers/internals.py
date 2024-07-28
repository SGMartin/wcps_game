import logging

from handlers.packet_handler import PacketHandler

from packets.internals import GameServerDetails

from wcps_core.constants import ErrorCodes

class AuthConnectionHandler(PacketHandler):
    async def process(self, server) -> None:
        await server.send(GameServerDetails().build())

class AuthorizeServerHandler(PacketHandler):
    async def process(self, server) -> None:
        error_code = int(self.get_block(0))

        error_messages = {
            ErrorCodes.SERVER_LIMIT_REACHED: "Max server capacity reached in authentication server",
            ErrorCodes.INVALID_SERVER_TYPE: "Invalid server type. Rejected by authentication server.",
            ErrorCodes.INVALID_SESSION_MATCH: "Authentication server does not recognize game server",
            ErrorCodes.ALREADY_AUTHORIZED: "Server already registered",
            ErrorCodes.SERVER_ERROR_OTHER: "Unknown error. Check game server credentials"
        }

        if error_code in error_messages:
            logging.error(error_messages[error_code])
            await server.disconnect()
            return

        if error_code == ErrorCodes.SUCCESS:
            session_id = self.get_block(1)

            if server.is_first_authorized:
                server.authorize(session_id=session_id)
            else:
                logging.info("Game Server reconnected to authentication. Update?")
                ##TODO: Update and sync routine
                server.authorize(session_id=session_id)
        else:
            logging.error(f"Unknown error {error_code}")
            await server.disconnect()
            return