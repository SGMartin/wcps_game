from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_game.handlers.packet_handler import PacketHandler

from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.packet_list import PacketList


class UserListHandler(PacketHandler):
    async def process(self, u: "User") -> None:

        if u.authorized:
            target_userlist_page = int(self.get_block(0))

            if target_userlist_page < 0:
                target_userlist_page = 0

            # Safe for max. 250 users
            if target_userlist_page > 27:
                target_userlist_page = 27

            u.userlist_page = target_userlist_page

            # TODO: filter those that are in the lobby / channel?
            # TODO: show newist players first
            lobby_users = await u.this_server.channels[u.channel].get_users()

            packet = PacketFactory.create_packet(
                packet_id=PacketList.DO_USER_LIST,
                lobby_user_list=lobby_users,
                target_page=target_userlist_page
                )
            await u.send(packet.build())
