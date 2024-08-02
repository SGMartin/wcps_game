import asyncio
import logging

from wcps_core.constants import Ports, ServerTypes
from wcps_game.entities import BaseNetworkEntity


class GameServer(BaseNetworkEntity):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):

        # Network data
        # TODO: configs here
        self.name = "WCPS"
        self.ip = "127.0.0.1"
        self.port = Ports.GAME_CLIENT

        # Game properties
        self.max_players = 3600
        self.current_rooms = 0
        self.id = 0
        self.server_type = ServerTypes.ENTIRE
        self.premium_only = False

        self.online_users = {}

        # Lock to ensure thread safety and asyncio safety
        self.lock = asyncio.Lock()
        
    async def add_player(self, u):
        async with self.lock:
            if not u.username:
                raise Exception("Attempt to add an unnamed user")
            if u.username in self.online_users:
                raise Exception(f"User {u.username} already exists")
            self.online_users[u.username] = u

    # TODO: send internal packet to auth
    async def remove_player(self, username):
        async with self.lock:
            if username in self.online_users:
                del self.online_users[username]
                logging.info(f"Removed player {username}")
            else:
                raise Exception(f"User {username} does not exist")

    async def is_online(self, username) -> bool:
        async with self.lock:
            return username in self.online_users

    def get_player_count(self) -> int:
        return len(self.online_users)

    async def get_player(self, username) -> 'User':
        async with self.lock:
            user = self.online_users.get(username)
            if user is None:
                raise Exception(f"User {username} not found")
            return user
