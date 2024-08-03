import asyncio
import logging
import time

from wcps_core.constants import Ports, ServerTypes, InternalKeys

from wcps_game.entities.network_entities import NetworkEntity
from wcps_game.handlers import get_handler_for_packet
from wcps_game.networking import ClientXorKeys


class User(NetworkEntity):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):

        # network properties
        self.reader = reader
        self.writer = writer
        self.xor_key_send = ClientXorKeys.SEND
        self.xor_key_receive = ClientXorKeys.RECEIVE

        # authorization properties
        self.authorized = False
        self.session_id = None
        self.internal_id = -1  # probably legacy but maybe the client uses it for some stuff?
        self.rights = -1
        self.username = None

        # game properties
        self.displayname = ""
        self.last_ping = time.time() * 1000  # milliseconds
        self.ping = 0
        self.is_updated_ping = True

    def get_handler_for_packet(self, packet_id):
        return get_handler_for_packet(packet_id)


class GameServer(NetworkEntity):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        super().__init__(
            reader=reader,
            writer=writer,
            xor_key_send=InternalKeys.XOR_GAME_SEND,
            xor_key_receive=InternalKeys.XOR_AUTH_SEND
            )

        # Network data
        # TODO: configs here
        self.name = "WCPS"
        self.ip = "127.0.0.1"
        self.port = Ports.GAME_CLIENT

        # Authorization properties
        self.is_first_authorized = True
        self.authorized = False
        self.session_id = None

        # Game properties
        self.max_players = 3600
        self.current_rooms = 0
        self.id = 0
        self.server_type = ServerTypes.ENTIRE
        self.premium_only = False

        self.online_users = {}

        # Lock to ensure thread safety and asyncio safety
        self.lock = asyncio.Lock()

    def get_handler_for_packet(self, packet_id):
        return get_handler_for_packet(packet_id)

    async def add_player(self, u: User):
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

    async def get_player(self, username) -> User:
        async with self.lock:
            user = self.online_users.get(username)
            if user is None:
                raise Exception(f"User {username} not found")
            return user 

    def authorize(self, session_id: int):
        self.session_id = session_id
        self.authorized = True
        self.is_first_authorized = False
