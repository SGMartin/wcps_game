from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_game.handlers.packet_handler import PacketHandler

from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.userlist import last_user_list_page


class UserListHandler(PacketHandler):
    async def process(self, u: "User") -> None:
        if not u.authorized:
            return

        # The page the client wants (PF23 0x46b130): its page -1 (min 0) or +1, with no upper limit
        target_page = max(0, int(self.get_block(0)))

        # TODO: filter those that are in the lobby / channel?
        # TODO: show newist players first
        channel = u.this_server.channels[u.channel]
        lobby_users = await channel.get_users()

        if target_page > last_user_list_page(len(lobby_users)):
            # Past the last page: count 0, the client keeps the page it shows
            packet = PacketFactory.create_packet(
                packet_id=PacketList.DO_USER_LIST, lobby_user_list=[], target_page=target_page
            )
            await u.send(packet.build())
            return

        u.userlist_page = target_page
        await channel.send_user_list(u, lobby_users)
