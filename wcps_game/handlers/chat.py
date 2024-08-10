import logging

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_game.handlers.packet_handler import PacketHandler
from wcps_game.game.constants import ChatChannel, RoomStatus
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory


class ChatHandler(PacketHandler):
    async def process(self, user: "User"):

        if user.authorized:
            message_channel = int(self.get_block(0))

            valid_message_channels = [
                ChatChannel.NOTICE1,
                ChatChannel.NOTICE2,
                ChatChannel.CLAN,
                ChatChannel.LOBBY2CHANNEL,
                ChatChannel.LOBBY2ALL,
                ChatChannel.ROOM2TEAM,
                ChatChannel.ROOM2ALL,
                ChatChannel.WHISPER
            ]

            if message_channel not in valid_message_channels:
                logging.error(f"Unknown message channel {message_channel}")
                return

            # IN:: 78194431 29696 3 0 NULL DarkRaptor>>asdasdsadadad
            receiver_id = self.get_block(1)
            receiver_name = self.get_block(2)
            in_message = self.get_block(3)

            # TODO: this could be a function
            try:
                message_delim = f">>{chr(0x1D)}"
                message_parts = in_message.split(message_delim)

                real_message = message_parts[1].replace(chr(0x1D), chr(0x20))
                real_message = real_message.strip()
            except:
                logging.warning(f"Invalid message {in_message}")
                return
            if len(real_message) > 60:
                logging.warning(f"Sent a too long message {real_message}")
                return

            if message_channel == ChatChannel.LOBBY2CHANNEL:  # TODO: check if the user is in a room
                this_packet = PacketFactory.create_packet(
                    packet_id=PacketList.CHAT,
                    error_code=1,
                    user=user,
                    chat_type=message_channel,
                    receiver_id=receiver_id,
                    receiver_username=receiver_name,
                    message=real_message
                )
                this_channel = user.this_server.channels[user.channel]
                await this_channel.broadcast_packet_to_channel(this_packet.build())

            if message_channel == ChatChannel.LOBBY2ALL:
                this_packet = PacketFactory.create_packet(
                    packet_id=PacketList.CHAT,
                    error_code=1,
                    user=user,
                    chat_type=message_channel,
                    receiver_id=receiver_id,
                    receiver_username=receiver_name,
                    message=real_message
                )
                await user.this_server.broadcast_packet_to_lobby(this_packet.build())

            if message_channel == ChatChannel.ROOM2TEAM:
                logging.info("ROOMS NOT YET IMPLEMENTED")
                return
            if message_channel == ChatChannel.ROOM2ALL:
                if user.room is not None:
                    if user.room.state == RoomStatus.WAITING and user.room.master == user and user.room.supermaster:
                        receiver_id = 998  # Sets text in yellow for supermaster

                    this_packet = PacketFactory.create_packet(
                        packet_id=PacketList.CHAT,
                        error_code=1,
                        user=user,
                        chat_type=message_channel,
                        receiver_id=receiver_id,
                        receiver_username=receiver_name,
                        message=real_message
                    )
                    await user.room.send(this_packet.build())

            if message_channel == ChatChannel.CLAN:
                logging.info("CLAN CHAT NOT READY YET")
                return

            if message_channel == ChatChannel.WHISPER:
                target_user = await user.this_server.get_player_by_displayname(receiver_name)
                # Separate display name from the following string
                receiver_name = receiver_name + chr(0x1D)
                if target_user is not None:
                    sender_packet = PacketFactory.create_packet(
                        packet_id=PacketList.CHAT,
                        error_code=1,
                        user=user,
                        chat_type=message_channel,
                        receiver_id=target_user.session_id,
                        receiver_username=receiver_name,
                        message=real_message
                    )
                    await user.send(sender_packet.build())

                    # Handles a stupid and harmless bug in client when you whisper yourself
                    if target_user != user:
                        await target_user.send(sender_packet.build())
                else:
                    error_packet = PacketFactory.create_packet(
                        packet_id=PacketList.CHAT,
                        user=user,
                        error_code=95040,  # TODO: Move this to an error code?
                        receiver_id=receiver_id,
                        receiver_username=receiver_name
                    )
                    await user.send(error_packet.build())

        else:
            await user.disconnect()
