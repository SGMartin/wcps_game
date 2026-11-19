import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room
    from wcps_game.game.game_server import User


from wcps_core.packets import OutPacket

from wcps_game.game.constants import ChannelType, RoomStatus
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.userlist import last_user_list_page


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
                await self.send_user_list(user, users_left)

    async def send_user_list(self, user: "User", channel_users: list = None):
        """Send the user their page of the lobby user list, moved back to the last page if the list
        got shorter (it is never empty: the user is in it)."""
        if channel_users is None:
            channel_users = await self.get_users()

        user.userlist_page = min(user.userlist_page, last_user_list_page(len(channel_users)))
        user_list = PacketFactory.create_packet(
            packet_id=PacketList.DO_USER_LIST,
            lobby_user_list=channel_users,
            target_page=user.userlist_page,
        )
        await user.send(user_list.build())

    async def get_users(self):
        async with self._users_lock:
            return list(self.users.values())

    async def get_all_rooms(self):
        async with self._rooms_lock:
            return {k: v for k, v in self.rooms.items() if v is not None}

    async def get_room_list_for(self, user: "User") -> list:
        """The rooms of this user's room list, as their filter shows them.

        All rooms (default): the rooms of user.room_page, ids page*8 .. page*8+7. The client puts each
        one in row 'id - page*8' of its 8-row table without a bounds check (PF20 0x4f69a0), so a room
        from another page would be written outside the table.
        Waiting only: up to 8 waiting rooms from user.room_list_anchor on, in id order. The client
        fills its rows one after another."""
        rooms = sorted((await self.get_all_rooms()).values(), key=lambda room: room.id)

        if not user.room_list_waiting:
            return [room for room in rooms if room.room_page == user.room_page]

        waiting = [room for room in rooms if room.state == RoomStatus.WAITING]
        return [room for room in waiting if room.id >= user.room_list_anchor][:8]

    async def send_room_list(self, user: "User"):
        room_list = PacketFactory.create_packet(
            packet_id=PacketList.DO_ROOM_LIST,
            room_page=user.room_page,
            room_list=await self.get_room_list_for(user),
            viewer=user,
        )
        await user.send(room_list.build())

    async def broadcast_packet_to_channel(self, packet: OutPacket):
        all_users = await self.get_users()

        for user in all_users:
            if user.room is None:
                await user.send(packet)
