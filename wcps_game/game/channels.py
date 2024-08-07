import asyncio

from wcps_game.game.constants import ChannelType


class Room:
    def __init__(self, name, channel: ChannelType, room_id: int = -1):
        # MOCK CLASS
        self.name = "MV"
        self.channel = Channel.CQC
        self.state = 1
        self.master = 2
        self.displayname = "HERIDOTE"
        self.has_password = 0
        self.maximum_players = 16
        self.player_count = 12
        self.map = 2
        self.mode = 7
        self.mode2 = 0
        self.timeleft = 0
        self.game_mode = 0
        self.joinable = 0
        self.supermaster = 0
        self.type = 0
        self.level_limit = 0
        self.premium = 0
        self.enable_kick = 0
        self.autostart = 0
        self.pinglimit = 1
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
            else:
                print("User not in channel")

    async def get_users(self):
        async with self._users_lock:
            return list(self.users.values())

    async def get_rooms(self):
        async with self._rooms_lock:
            return {k: v for k, v in self.rooms.items() if v is not None}