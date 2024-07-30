import asyncio
import struct
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
                        handler = get_handler_for_packet(incoming_packet.packet_id, self.game_server, self)
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
    
    ##TODO: Improve this right here
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

# XOR keys for encryption/decryption
# Opposite of the usual client keys

class UDP_XORKEYS():
    XOR_SEND_KEY = 0xC3
    XOR_RECEIVE_KEY = 0x96

class UDPListener:
    def __init__(self, port):
        self.port = port
        self.transport = None
        self.protocol = None

    async def start(self):
        loop = asyncio.get_running_loop()
        self.transport, self.protocol = await loop.create_datagram_endpoint(
            lambda: UDPProtocol(self), local_addr=('0.0.0.0', self.port))
        logger.info(f"UDP listener started on port {self.port}")

    def reverse_port(self, port):
        """Reverses the byte order of the port number."""
        return struct.unpack(">H", struct.pack("<H", port))[0]

    def handle(self, packet, addr):
        """Handles incoming UDP packets and logs decrypted content."""
        decrypted_packet = self.decrypt_packet(packet)
        packet_type = self.to_ushort(decrypted_packet, 0)
        session_id = self.to_ushort(decrypted_packet, 4)

        # Log decrypted packet
        logger.info(f"Received packet from {addr} with type {hex(packet_type)} and session ID {session_id}")

        # Simulate user retrieval (replace with your user matching logic)
        user = self.match_user(session_id)

        if user is None:
            return

        if packet_type == 0x1001:  # Initial packet
            decrypted_packet = self.write_ushort(self.port + 1, decrypted_packet, 4)
            self.protocol.send_to(decrypted_packet, addr)

        elif packet_type == 0x1010:  # UDP Ping packet
            if decrypted_packet[14] == 0x21:
                user.local_end_point = self.to_ip_endpoint(decrypted_packet, 32)
                user.remote_end_point = addr
                user.remote_port = self.reverse_port(addr[1])
                user.local_port = self.reverse_port(user.local_end_point[1])

                response = bytearray(65)
                response[17] = 0x41
                response[-1] = 0x11
                self.write_ushort(user.session_id, response, 4)
                self.write_ip_endpoint(user.remote_end_point, response, 32)
                self.write_ip_endpoint(user.local_end_point, response, 50)
                self.protocol.send_to(response, addr)

        elif decrypted_packet[14] in (0x10, 0x30, 0x31, 0x32, 0x34):
            if user.room is None:
                return
            
            session_id_bytes = decrypted_packet[4:6]
            target_id = self.to_ushort(decrypted_packet, 22)
            room = self.to_ushort(decrypted_packet, 6)
            session_id = struct.unpack("<H", session_id_bytes)[0]
            
            user1 = self.match_user(session_id)
            user2 = self.match_user(target_id)

            if (user1 and user2 and user1.room.id == room and user2.room.id == room and
                user1.room.state == 'Playing'):
                self.protocol.send_to(decrypted_packet, user2.remote_end_point)
            else:
                logger.error(f"UDP TUNNEL PACKET FAULTY - ROOM DID NOT MATCH SENDER {user1.displayname}/{user2.displayname}/"
                             f"{user1.room.id}/{user2.room.id}/{room}")

        else:
            logger.error(f"UNHANDLED UDP SUB PACKET {decrypted_packet[14]}")

    def decrypt_packet(self, packet):
        """Decrypts the packet using the XOR key."""
        decrypted_packet = bytearray(packet)
        for i in range(len(decrypted_packet)):
            decrypted_packet[i] ^= UDP_XORKEYS.XOR_RECEIVE_KEY
        return decrypted_packet

    def to_ushort(self, data, offset):
        """Converts bytes to a ushort (2 bytes)."""
        return struct.unpack(">H", data[offset:offset + 2])[0]

    def to_uint(self, data, offset):
        """Converts bytes to a uint (4 bytes)."""
        return struct.unpack(">I", data[offset:offset + 4])[0]

    def to_ip_endpoint(self, data, offset):
        """Converts bytes to an IP endpoint (IP address and port)."""
        for i in range(offset, offset + 6):
            data[i] ^= UDP_XORKEYS.XOR_SEND_KEY
        port = self.to_ushort(data, offset)
        ip = self.to_uint(data, offset + 2)
        return (ip, port)

    def write_ushort(self, value, data, offset):
        """Writes a ushort (2 bytes) to the data at the specified offset."""
        struct.pack_into(">H", data, offset, value)

    def write_uint(self, value, data, offset):
        """Writes a uint (4 bytes) to the data at the specified offset."""
        struct.pack_into(">I", data, offset, value)

    def write_ip_endpoint(self, endpoint, data, offset):
        """Writes an IP endpoint (IP address and port) to the data at the specified offset."""
        ip, port = endpoint
        value = bytearray(6)
        self.write_ushort(port, value, 0)
        struct.pack_into(">I", value, 2, ip)
        for i in range(6):
            data[offset + i] = value[i] ^ UDP_XORKEYS.XOR_RECEIVE_KEY

    def match_user(self, session_id):
        """Simulate user retrieval by session ID (replace with your logic)."""
        # Implement user retrieval logic here
        return None

class UDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, listener):
        self.listener = listener

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        self.listener.handle(data, addr)

    def send_to(self, data, addr):
        self.transport.sendto(data, addr)

## Start TCP listeners here
async def start_listeners(this_server: 'GameServer', this_auth: AuthenticationClient):
    try:
        tcp_server = await asyncio.start_server(
            lambda reader,writer: User(reader, writer, this_server, this_auth), this_server.ip, this_server.port)
        logging.info("TCP listener started.")
    except OSError:
        logging.error(f"Failed to bind to port {wcps_core.constants.Ports.AUTH_CLIENT}")
        return
    await asyncio.gather(tcp_server.serve_forever())
