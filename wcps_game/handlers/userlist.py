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

            u.user_list_page = target_userlist_page

            # TODO: filter those that are in the lobby / channel?
            # TODO: show newist players first
            lobby_users = list(u.this_server.online_users.values())

            packet = PacketFactory.create_packet(
                packet_id=PacketList.USERLIST,
                lobby_user_list=lobby_users,
                target_page=target_userlist_page
                )
            await u.send(packet.build())
