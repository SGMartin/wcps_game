from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_game.handlers.packet_handler import PacketHandler
from wcps_game.game.constants import ChannelType
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory


class SelectChannelHandler(PacketHandler):
    async def process(self, user: "User"):
        if user.authorized:
            print(f"User current channel is {user.channel}")
            target_channel = int(self.get_block(0))
            print(f"User target channel is {target_channel}")
            if target_channel <= ChannelType.BATTLEGROUP:  # min. channel 0 max channel BG
                # Check if the user was previously in any channel
                if user.channel > 0:
                    await user.this_server.channels[user.channel].remove_user(user)

                # TODO: move this to user/channel class and implement upper bounds
                await user.this_server.channels[target_channel].add_user(user)
                user.channel = target_channel
                user.userlist_page = 0

                channel_change = PacketFactory.create_packet(
                    packet_id=PacketList.SELECT_CHANNEL,
                    target_channel=target_channel
                )
                await user.send(channel_change.build())

                # Send userlist for this channel
                all_channel_users = await user.this_server.channels[target_channel].get_users()

                for channel_member in all_channel_users:
                    if channel_member.room is None:
                        userlist = PacketFactory.create_packet(
                            packet_id=PacketList.USERLIST,
                            lobby_user_list=all_channel_users,
                            target_page=channel_member.userlist_page
                            )
                        print(userlist.blocks)
                        logging.info(f"Updated {len(all_channel_users)} channel userlist for {channel_member.displayname}")
                        await channel_member.send(userlist.build())

                # from wcps_game.game.channels import Room

                # fake_room_list = []

                # for i in range(0, 101):
                #     this_room = Room(f"room {i}", 1, i)
                #     fake_room_list.append(this_room)

                # fake_room_packet = PacketFactory.create_packet(
                #     packet_id=PacketList.ROOMLIST,
                #     room_page=0,
                #     room_list=fake_room_list[0:7]
                # )
                # await user.send(fake_room_packet.build())

        else:
            await user.disconnect()
