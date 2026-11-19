from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_game.handlers.packet_handler import PacketHandler
from wcps_game.game.constants import ChannelType
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory


class SelectChannelHandler(PacketHandler):
    async def process(self, user: "User"):
        if user.authorized:
            target_channel = int(self.get_block(0))
            if target_channel <= ChannelType.BATTLEGROUP:  # min. channel 0 max channel BG
                # Check if the user was previously in any channel
                if user.channel > 0:
                    await user.this_server.channels[user.channel].remove_user(user)

                # TODO: move this to user/channel class and implement upper bounds
                await user.this_server.channels[target_channel].add_user(user)
                user.channel = target_channel
                user.userlist_page = 0
                user.room_page = 0
                user.room_list_waiting = False  # the client starts the lobby on all rooms, page 0

                channel_change = PacketFactory.create_packet(
                    packet_id=PacketList.DO_SET_CHANNEL,
                    target_channel=target_channel
                )
                await user.send(channel_change.build())

                # Send userlist for this channel
                # TODO: Move this and the user list to channel class????
                all_channel_users = await user.this_server.channels[target_channel].get_users()

                for channel_member in all_channel_users:
                    if channel_member.room is None:
                        await user.this_server.channels[target_channel].send_user_list(
                            channel_member, all_channel_users
                        )

                # Send the room list to the user: page 0, ids 0-7 (not the first 8 rooms that exist: with
                # gaps, those could include ids 8+ and the client would write them outside its table)
                await user.this_server.channels[target_channel].send_room_list(user)
        else:
            await user.disconnect()
