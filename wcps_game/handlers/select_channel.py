from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_game.handlers.packet_handler import PacketHandler
from wcps_game.game.constants import ChannelType
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory


class SelectChannel(PacketHandler):
    async def process(self, user: "User"):
        if user.authorized:

            target_channel = int(self.get_block(0))

            if target_channel <= ChannelType.BATTLEGROUP:  # min. channel 0 max channel BG
                user.channel = target_channel

                channel_change = PacketFactory.create_packet(
                    packet_id=PacketList.SELECT_CHANNEL,
                    target_channel=target_channel
                )
                await user.send(channel_change.build())

                from wcps_game.game.channels import Room

                fake_room_list = []

                for i in range(0, 101):
                    this_room = Room(f"room {i}", 1, i)
                    fake_room_list.append(this_room)

                fake_room_packet = PacketFactory.create_packet(
                    packet_id=PacketList.ROOMLIST,
                    room_page=0,
                    room_list=fake_room_list[0:7]
                )
                await user.send(fake_room_packet.build())

        else:
            await user.disconnect()
