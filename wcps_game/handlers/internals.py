import logging

from handlers.packet_handler import PacketHandler

from packets.internals import GameServerDetails

from wcps_core.constants import ErrorCodes

class AuthConnectionHandler(PacketHandler):
    async def process(self, server) -> None:
        await server.send(GameServerDetails(self.this_server).build())

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

class AuthorizePlayerHandler(PacketHandler):
    async def process(self, server) -> None:

        ## import a needed packet locally
        from packets.server import PlayerAuthorization
        
        error_code = int(self.get_block(0))
        reported_user = self.get_block(1)
        reported_session_id = int(self.get_block(2))
        reported_rights = int(self.get_block(3))

        ## get user 
        this_user = await self.this_server.get_player(reported_user)

        if not this_user:
            logging.error("Unknown player to authorize {reported_user}")
        else:
            ## TODO: implement update in the future if needed
            if error_code == ErrorCodes.SUCCESS or ErrorCodes.UPDATE:
                await this_user.authorize(
                    username=reported_user,
                    session_id=reported_session_id,
                    reported_rights=reported_rights
                    )
            else:
                await this_user.send(PlayerAuthorization(error_code).build())
                await this_user.disconnect()
 