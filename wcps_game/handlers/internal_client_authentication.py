import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import GameServer

from wcps_core.constants import ErrorCodes

from wcps_game.handlers.packet_handler import PacketHandler
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.error_codes import PlayerAuthorizationError


class AuthorizeClientHandler(PacketHandler):
    async def process(self, server: "GameServer") -> None:

        error_code = int(self.get_block(0))
        reported_user = self.get_block(1)
        reported_session_id = int(self.get_block(2))
        reported_rights = int(self.get_block(3))

        # get user
        this_user = await server.get_player(reported_user)

        if not this_user:
            logging.error("Unknown player to authorize {reported_user}")
            this_user.disconnect()
        else:
            # TODO: implement update in the future if needed
            if error_code == ErrorCodes.SUCCESS or error_code == ErrorCodes.UPDATE:
                await this_user.authorize(
                    username=reported_user,
                    session_id=reported_session_id,
                    rights=reported_rights
                    )
            
                packet = PacketFactory.create_packet(
                    packet_id=PacketList.PLAYER_AUTHORIZATION,
                    error_code=ErrorCodes.SUCCESS,
                    u=this_user
                )
                await this_user.send(packet.build())
            else:
                packet = PacketFactory.create_packet(
                    packet_id=PacketList.PLAYER_AUTHORIZATION,
                    error_code=PlayerAuthorizationError.NORMAL_PROCEDURE
                    )
                await this_user.send(packet.build())
                await this_user.disconnect()
