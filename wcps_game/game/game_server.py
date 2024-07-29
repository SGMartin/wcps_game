import asyncio
import logging

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
            if not u.authorized:
                raise Exception(f"Attempt to add an unauthorized user {u.username}")
            if u.session_id in self.online_users:
                raise Exception("User already exists")
            self.online_users[u.session_id] = u

    async def remove_player(self, session_id):
        async with self.lock:
            if session_id in self.online_users:
                del self.online_users[session_id]
            else:
                raise Exception(f"User with session ID {session_id} does not exist")

    async def is_online(self, session_id) -> bool:
        async with self.lock:
            return session_id in self.online_users

    def get_player_count(self) -> int:
        return len(self.online_users)

    async def get_player(self, session_id) -> 'User':
        async with self.lock:
            user = self.online_users.get(session_id)
            if user is None:
                raise Exception(f"User with session ID {session_id} not found")
            return user
class User:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, this_server:GameServer):
        ## network related tasks
        self.reader = reader
        self.writer = writer

        ## game related tasks
        self.this_server = this_server
        self.authorized = False
        self.session_id = None
        self.rights = -1

        

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
                    handler = get_handler_for_packet(incoming_packet.packet_id, self.this_server)
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


    async def authorize(self, session_id:int, rights: int):
        self.session_id = session_id
        self.rights = rights
        self.authorized = True
