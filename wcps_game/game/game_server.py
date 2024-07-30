import asyncio
import logging
import time

from typing import TYPE_CHECKING, Dict

from wcps_core.constants import Ports, ServerTypes
from wcps_core.packets import InPacket, Connection


if TYPE_CHECKING:
    from packets.internals import GameServerDetails

class ClientXorKeys:
    SEND = 0x96
    RECEIVE = 0xC3

class GameServer:
    def __init__(self):
        ## Network data
        self.name = "WCPS"
        self.ip = "127.0.0.1"
        self.port = Ports.GAME_CLIENT
        ## Game properties
        self.max_players = 0
        self.current_rooms = 0
        self.id = 0
        self.server_type = ServerTypes.ENTIRE
        self.premium_only = True

        self.online_users = {}  #
        self.lock = asyncio.Lock() # Lock to ensure thread safety and asyncio safety

    async def add_player(self, u):
        async with self.lock:
            if not u.username:
                raise Exception(f"Attempt to add an unnamed user")
            if u.username in self.online_users:
                raise Exception("User already exists")
            self.online_users[u.username] = u

    #TODO: send internal packet to auth
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
class User:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, this_server:GameServer, this_auth):
        ## network related tasks
        self.reader = reader
        self.writer = writer
        self.this_auth = this_auth

        ## auth related tasks
        self.this_server = this_server
        self.authorized = False
        self.session_id = None
        self.rights = -1
        self.username = None
        
        ## game related tasks
        self.last_ping = time.time() * 1000 ## milliseconds
        self.ping = 0
        self.is_updated_ping = True


        ## Send a connection packet to the client
        asyncio.create_task(self.send(Connection(xor_key=ClientXorKeys.SEND).build()))

        ## Start listening for client packets
        asyncio.create_task(self.listen())

    async def listen(self):
        from handlers.handler_list import get_handler_for_packet
        while True:
            data = await self.reader.read(1024)
            if not data:
                await self.disconnect()
                break

            try:
                incoming_packet = InPacket(buffer=data, receptor=self, xor_key=ClientXorKeys.RECEIVE)
                if incoming_packet.decoded_buffer:
                    logging.info(f"IN:: {incoming_packet.decoded_buffer}")
                    handler = get_handler_for_packet(incoming_packet.packet_id, self.this_server, self.this_auth)
                    if handler:
                        asyncio.create_task(handler.handle(incoming_packet))
                    else:
                        logging.error(f"Unknown handler for packet {incoming_packet.packet_id}")
                else:
                    logging.error(f"Cannot decrypt packet {incoming_packet}")
                    await self.disconnect()
            except Exception as e:
                logging.exception(f"Error processing packet: {e}")
                await self.disconnect()
                break

    async def send(self, buffer):
        try:
            self.writer.write(buffer)
            await self.writer.drain()
        except Exception as e:
            logging.exception(f"Error sending packet: {e}")
            await self.disconnect()
    
    async def disconnect(self):
        logging.info("Closing connection to client")
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.reader = None
        self.writer = None

        if self.authorized:
            self.authorized = False
            await self.this_server.remove_player(self.username)


    async def authorize(self, username:str, session_id:int, rights: int):
        self.username = username
        self.session_id = session_id
        self.rights = rights
        self.authorized = True

        ##TODO: In the future, verify premium status for premium only servers
        from packets.server import PlayerAuthorization, Ping

        await self.send(PlayerAuthorization(1, self).build())
        await self.send_ping()
    
    async def answer_ping(self):
        self.is_updated_ping = True
        self.ping = round(time.time() * 1000 - self.last_ping)
    
    async def send_ping(self):
        from packets.server import Ping
        if not self.is_updated_ping:
            logging.info(f"Disconnected {self.username} because of bad ping")
            await self.disconnect()
        else:
            #TODO: update premium time here
            self.is_updated_ping = False
            await self.send(Ping(self).build())


