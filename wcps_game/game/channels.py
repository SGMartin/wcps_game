import asyncio

from wcps_core.packets import OutPacket

from wcps_game.game.constants import ChannelType
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory


class Room:
    def __init__(self, name, channel: ChannelType, room_id: int = -1):
        # MOCK CLASS
        self.name = "MV"
        self.channel = ChannelType.CQC
        self.state = 2
        self.master = 2
        self.displayname = "VIVA SINSO"
        self.has_password = 0
        self.maximum_players = 16
        self.player_count = 12
        self.map = 15
        self.mode = 0
        self.mode2 = 0
        self.timeleft = 0
        self.game_mode = 0
        self.joinable = 1
        self.supermaster = 0
        self.type = 0
        self.level_limit = 0
        self.premium = 0
        self.enable_kick = 1
        self.autostart = 1
        self.pinglimit = 2
        self.clanwar = -1


class Channel:
    def __init__(self, channel_type: ChannelType):

        self.type = channel_type
        self.users = {}
        self.rooms = dict.fromkeys(range(0, 101))  # Let's limit the rooms to 100 for now
        self._users_lock = asyncio.Lock()
        self._rooms_lock = asyncio.Lock()

    async def add_room(self, new_room: Room):
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
                print("User already in channel")

    async def remove_user(self, user):
        async with self._users_lock:
            if user.username in self.users:
                del self.users[user.username]

                users_left = await self.get_users()
                for user in users_left:
                    new_user_list = PacketFactory.create_packet(
                        packet_id=PacketList.USERLIST,
                        lobby_user_list=users_left,
                        target_page=users_left.userlist_page
                    )
                    await user.send(new_user_list.build())
            else:
                print("User not in channel")

    async def get_users(self):
        async with self._users_lock:
            return list(self.users.values())

    async def get_rooms(self):
        async with self._rooms_lock:
            return {k: v for k, v in self.rooms.items() if v is not None}

    async def broadcast_packet_to_channel(self, packet: OutPacket):
        all_users = await self.get_users()

        for user in all_users:
            if user.room is None:
                await user.send(packet)
