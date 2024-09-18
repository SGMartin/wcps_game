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
                        userlist = PacketFactory.create_packet(
                            packet_id=PacketList.USERLIST,
                            lobby_user_list=all_channel_users,
                            target_page=channel_member.userlist_page
                            )
                        await channel_member.send(userlist.build())

                # Send the room list to the user
                all_rooms_channel = await user.this_server.channels[target_channel].get_all_rooms()

                # Send only the first 8 rooms since it's page 1
                first_page_rooms = list(all_rooms_channel.values())[0:8]

                room_list = PacketFactory.create_packet(
                    packet_id=PacketList.DO_ROOM_LIST,
                    room_page=0,
                    room_list=first_page_rooms
                )
                await user.send(room_list.build())
        else:
            await user.disconnect()
