import asyncio
import logging

from typing import TYPE_CHECKING

import wcps_core.constants
import wcps_core.packets

from packets.internals import GameServerStatus

if TYPE_CHECKING:
    from game.game_server import GameServer
    from handlers.handler_list import get_handler_for_packet

from game.game_server import User

# Import get_handler_for_packet for runtime use
from handlers.handler_list import get_handler_for_packet

class AuthenticationClient:
    def __init__(self, this_server: 'GameServer'):
        ## network (internal)
        self._stop_event = asyncio.Event()  # Event to signal stop
        self.ip = "127.0.0.1"
        self.port = 5012
        self.reader = None
        self.writer = None
        self.max_retries = 5
        self._stop_event = asyncio.Event()  # Event to signal stop

        ## related to gameserver... move there?
        self.session_id = -1
        self.authorized = False
        self.is_first_authorized = True
        self.game_server = this_server

    async def connect(self):
        attempt = 0
        while attempt < self.max_retries:
            try:
                self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
                logging.info(f'Connected to auth server at {self.ip}:{self.port}')
                return
            except Exception as e:
                attempt += 1
                logging.error(f"Error connecting to auth server (attempt {attempt}/{self.max_retries}): {e}")
                await asyncio.sleep(2)  # Wait for 2 seconds before retrying
        logging.error("Failed to connect after several attempts.")
        raise ConnectionError("Unable to connect to the auth server.")

    async def send(self, buffer):
        if self.writer is None:
            raise ConnectionError("Client is not connected. Call 'connect' first.")

        try:
            self.writer.write(buffer)
            await self.writer.drain()
        except Exception as e:
            logging.error(f"Error sending packet: {e}")
            await self.disconnect()
            #await self.reconnect()

    async def listen(self):
        if self.reader is None:
            raise ConnectionError("Client is not connected. Call 'connect' first.")

        while not self._stop_event.is_set():  # Check stop event
            try:
                data = await self.reader.read(1024)
                if not data:
                    await self.disconnect()
                    #await self.reconnect()
                    continue
                else:
                    incoming_packet = wcps_core.packets.InPacket(
                        buffer=data, 
                        receptor=self,
                        xor_key=wcps_core.constants.InternalKeys.XOR_AUTH_SEND
                    )
                    if incoming_packet.decoded_buffer:
                        print(f"IN:: {incoming_packet.decoded_buffer}")
                        handler = get_handler_for_packet(incoming_packet.packet_id, self.game_server)
                        if handler is not None:
                            asyncio.create_task(handler.handle(incoming_packet))
                        else:
                            print(f"Unknown handler for packet {incoming_packet.packet_id}")
            except Exception as e:
                logging.error(f"Error during listening: {e}")
                await self.disconnect()

    async def disconnect(self):
        logging.info("Closing connection to authentication server")
        self._stop_event.set()  # Signal to stop the listening loop
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.reader = None
        self.writer = None

    async def reconnect(self):
        attempt = 0
        while attempt < self.max_retries:
            try:
                await self.connect()
                return
            except Exception as e:
                attempt += 1
                logging.error(f"Error reconnecting to auth server (attempt {attempt}/{self.max_retries}): {e}")
                await asyncio.sleep(2)
        logging.error("Failed to reconnect after several attempts.")
        raise ConnectionError("Unable to reconnect to the auth server.")

    async def start_listening(self):
        while True:
            try:
                await self.listen()
            except Exception as e:
                logging.error(f"Error in listening loop: {e}")
                await self.reconnect()

    async def run(self):
        await self.connect()
        # Start listening in the background
        listening_task = asyncio.create_task(self.start_listening())
        await listening_task
    
    def authorize(self, session_id: int):
        self.session_id = session_id
        self.authorized = True
        self.is_first_authorized = False
    
    async def ping_authentication_server(self):
        while True:
            if self.authorized:
                ping_packet = GameServerStatus(self.game_server).build()
                await self.send(ping_packet)
            await asyncio.sleep(30)


## Start TCP and UDP listeners here
async def start_listeners(this_server: 'GameServer'):
    try:
        tcp_server = await asyncio.start_server(
            lambda reader,writer: User(reader, writer, this_server), this_server.ip, this_server.port)
        logging.info("TCP listener started.")
    except OSError:
        logging.error(f"Failed to bind to port {wcps_core.constants.Ports.AUTH_CLIENT}")
        return

    # try:
    #     server_listener = await asyncio.start_server(GameServer, "127.0.0.1", wcps_core.constants.Ports.INTERNAL)
    #     logging.info("Server listener started.")
    # except OSError:
    #     logging.error(f"Failed to bind to port {wcps_core.constants.Ports.INTERNAL}")
    #     return

    await asyncio.gather(tcp_server.serve_forever())
