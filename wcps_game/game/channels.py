import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room
    from wcps_game.game.game_server import User


from wcps_core.packets import OutPacket

from wcps_game.game.constants import ChannelType
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory


class Channel:
    def __init__(self, channel_type: ChannelType):

        self.type = channel_type
        self.users = {}
        self.rooms = dict.fromkeys(range(0, 101))  # Let's limit the rooms to 100 for now
        self._users_lock = asyncio.Lock()
        self._rooms_lock = asyncio.Lock()

    async def add_room(self, new_room: "Room"):
        async with self._rooms_lock:
            for slot, room in self.rooms.items():
                if room is None:
                    self.rooms[slot] = new_room
                    return slot
            # Could not find an empty slot for this room
            return None

    async def remove_room(self, room_id: int):
        async with self._rooms_lock:
            if 0 <= room_id < len(self.rooms) and self.rooms[room_id] is not None:
                self.rooms[room_id] = None

    async def add_user(self, user):
        async with self._users_lock:
            if user.username not in self.users:
                self.users[user.username] = user
            else:
                logging.info("User {user.displayname} already in the channel")

    async def remove_user(self, user: "User"):
        async with self._users_lock:
            if user.username in self.users:
                del self.users[user.username]
            else:
                logging.info(f"User {user.displayname} not in channel")

        users_left = await self.get_users()
        for user in users_left:
            if user.room is None:
                new_user_list = PacketFactory.create_packet(
                    packet_id=PacketList.DO_USER_LIST,
                    lobby_user_list=users_left,
                    target_page=user.userlist_page
                    )
                await user.send(new_user_list.build())

    async def get_users(self):
        async with self._users_lock:
            return list(self.users.values())

    async def get_all_rooms(self):
        async with self._rooms_lock:
            return {k: v for k, v in self.rooms.items() if v is not None}

    async def broadcast_packet_to_channel(self, packet: OutPacket):
        all_users = await self.get_users()

        for user in all_users:
            if user.room is None:
                await user.send(packet)
