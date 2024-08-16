import asyncio
import struct
import logging
from typing import Tuple, Optional, TYPE_CHECKING
import sys

from wcps_core.constants import Ports
from wcps_game.game.constants import RoomStatus
from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.packet_list import PacketList, ClientXorKeys

if TYPE_CHECKING:
    from wcps_game.game.game_server import GameServer


class ClientXorKeys:
    SEND = 0x96
    RECEIVE = 0xC3


class AuthenticationClient:
    def __init__(self, ip: str, port: int, max_retries: int = 5):
        self.ip = ip
        self.port = port
        self.max_retries = max_retries
        self.reader = None
        self.writer = None
        self._stop_event = asyncio.Event()

    async def connect(self):
        attempt = 0
        while attempt < self.max_retries:
            try:
                self.reader, self.writer = await asyncio.open_connection(
                    self.ip, self.port
                )
                logging.info(
                    f"Connection to authentication server at {self.ip}:{self.port}"
                )
                return self.reader, self.writer
            except Exception as e:
                attempt += 1
                logging.error(
                    f"Error connecting to Auth server (attempt {attempt}/{self.max_retries}): {e}"
                )
                # TODO: configure this...
                await asyncio.sleep(2)
        logging.error("Failed to connect after several attempts.")
        raise ConnectionError("Unable to connect to the auth server.")

    async def disconnect(self):
        logging.info("Closing connection to authentication server")
        self._stop_event.set()
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.reader = None
        self.writer = None

    async def reconnect(self):
        await self.disconnect()
        await self.connect()


class UDPListener:
    XOR_SEND_KEY = 0xC3
    XOR_RECEIVE_KEY = 0x96

    def __init__(self, port: int, server: "GameServer"):
        self.port = port
        self.game_server = server
        self.transport: Optional[asyncio.DatagramTransport] = None
        self.stop_event = asyncio.Event()

    async def start(self):
        """Start the UDP listener on the specified port."""
        try:
            loop = asyncio.get_event_loop()
            self.transport, _ = await loop.create_datagram_endpoint(
                lambda: UDPProtocol(self), local_addr=("0.0.0.0", self.port)
            )
            logging.info(f"UDP server listening on port {self.port}")
            await self.stop_event.wait()
        except Exception as e:
            logging.error(f"Failed to start UDP listener on port {self.port}: {e}")
            raise SystemExit("Aborting due to UDP listener failure.")

    async def stop(self):
        """Stop the UDP listener gracefully."""
        logging.info(f"Stopping UDP server on port {self.port}")
        if self.transport:
            self.transport.close()
            await self.transport.wait_closed()
        self.stop_event.set()

    async def handle_packet(self, packet: bytes, addr: Tuple[str, int]):
        """Handle incoming packets."""
        packet = bytearray(packet)
        type_ = self.to_ushort(packet, 0)
        session_id = self.to_ushort(packet, 4)

        this_user = self.game_server.get_player_by_session(session_id)

        if this_user is None:
            return

        # logging.info(f"IN:: UDP packet of type {type_} with session ID {session_id}")

        if type_ == 0x1001:  # Initial packet
            self.write_ushort(self.port + 1, packet, 4)
            self.transport.sendto(packet, addr)
        elif type_ == 0x1010:  # UDP Ping packet
            if packet[14] == 0x21:
                this_user.local_end_point = self.to_ip_endpoint(packet, 32)
                this_user.remote_end_point = addr
                this_user.remote_port = self.reverse_port(addr)
                this_user.local_port = self.reverse_port(this_user.local_end_point)

                response = self.extend(packet, 65)
                response[17] = 0x41
                response[-1] = 0x11
                self.write_ushort(this_user.session_id, response, 4)
                self.write_ip_endpoint(this_user.remote_end_point, response, 32)
                self.write_ip_endpoint(this_user.local_end_point, response, 50)
                self.transport.sendto(response, addr)

                room_id = self.to_ushort(packet, 6)

                # Temporal test to try to keep the player updated of rooms while training
                if room_id == 999:
                    rooms = await this_user.this_server.channels[this_user.channel].get_all_rooms()
                    rooms = [room for room in rooms.values() if room.room_page == this_user.room_page]

                    room_list = PacketFactory.create_packet(
                        packet_id=PacketList.DO_ROOM_LIST,
                        room_page=this_user.room_page,
                        room_list=rooms
                    )
                    await this_user.send(room_list.build())

            elif packet[14] in {0x10, 0x30, 0x31, 0x32, 0x34}:

                session_id_bytes = packet[4:6][::-1]  # Reverse the bytes to match the C# code
                target_id = self.to_ushort(packet, 22)
                room_id = self.to_ushort(packet, 6)
                session_id = struct.unpack("<H", session_id_bytes)[0]

                if this_user.room is None and room_id != 999:  # Training is 999
                    return

                U2 = self.game_server.get_player_by_session(target_id)

                if room_id == 999:  # He is training, set up special tunnel
                    U1 = U2
                    this_user.set_room(None, 999)
                else:
                    U1 = self.game_server.get_player_by_session(session_id)
                    if (
                        U1 is not None and U2 is not None and
                        U1.room.id == room_id and U2.room.id == room_id and
                        U1.room.state == RoomStatus.PLAYING
                    ):
                        self.transport.sendto(packet, U2.remote_end_point)
                    else:
                        logging.error(
                            f"UDP TUNNEL PACKET FAULTY - ROOM DID NOT MATCH SENDER "
                            f"{U1.displayname if U1 else 'None'}/"
                            f"{U2.displayname if U2 else 'None'}/"
                            f"{U1.room.id if U1 else 'None'}/"
                            f"{U2.room.id if U2 else 'None'}/"
                            f"{room_id}"
                        )
            else:
                logging.error(f"Unhandled UDP sub-packet {packet[14]:02x}")
        else:
            logging.error(f"Unhandled UDP packet type {type_}")

    def to_ushort(self, data: bytes, offset: int) -> int:
        """Convert bytes to ushort with big-endian."""
        return struct.unpack(">H", data[offset: offset + 2])[0]

    def write_ushort(self, value: int, data: bytearray, offset: int):
        """Write ushort value to bytearray at specified offset."""
        struct.pack_into(">H", data, offset, value)

    def to_ip_endpoint(self, data: bytes, offset: int) -> Tuple[str, int]:
        """Convert bytes to IPEndPoint."""
        for i in range(offset, offset + 6):
            data[i] ^= self.XOR_SEND_KEY
        port = self.to_ushort(data, offset)
        ip = struct.unpack(">I", data[offset + 2: offset + 6])[0]
        ip_address = (
            f"{(ip >> 24) & 0xFF}.{(ip >> 16) & 0xFF}.{(ip >> 8) & 0xFF}.{ip & 0xFF}"
        )
        return ip_address, port

    def write_ip_endpoint(
        self, endpoint: Tuple[str, int], data: bytearray, offset: int
    ) -> bytearray:
        """Write IPEndPoint to bytearray at specified offset with big-endian and XOR."""
        ip_address, port = endpoint
        port_bytes = struct.pack(">H", port)
        ip_bytes = struct.pack(
            ">I",
            int(ip_address.split(".")[0]) << 24
            | int(ip_address.split(".")[1]) << 16
            | int(ip_address.split(".")[2]) << 8
            | int(ip_address.split(".")[3]),
        )
        value = port_bytes + ip_bytes
        value = bytearray(b ^ self.XOR_RECEIVE_KEY for b in value)
        data[offset: offset + 6] = value
        return data

    def reverse_port(self, addr: Tuple[str, int]) -> int:
        """Reverse port to match the C# implementation."""
        return struct.unpack(">H", struct.pack("<H", addr[1]))[0]

    def extend(self, packet: bytes, length: int) -> bytearray:
        """Extend packet to a new length."""
        new_packet = bytearray(length)
        new_packet[: len(packet)] = packet
        return new_packet


class UDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, listener: UDPListener):
        self.listener = listener

    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        """Called when a datagram is received."""
        asyncio.ensure_future(self.listener.handle_packet(data, addr))

    def error_received(self, exc: Exception):
        """Handle any errors."""
        logging.error(f"Error received: {exc}")
        if self.listener.transport:
            self.listener.transport.close()


async def start_udp_listeners(server: "GameServer"):
    # Initialize UDP listeners
    udp_listener_1 = UDPListener(Ports.UDP1, server=server)
    udp_listener_2 = UDPListener(Ports.UDP2, server=server)

    try:
        # Start both UDP listeners as separate tasks
        udp_task1 = asyncio.create_task(udp_listener_1.start())
        udp_task2 = asyncio.create_task(udp_listener_2.start())

        # Gather both tasks, so the function will await indefinitely
        await asyncio.gather(udp_task1, udp_task2)
    except Exception as e:
        logging.error(f"Failed to start UDP listeners: {e}")
        sys.exit(1)  # Use sys.exit() to exit if an exception occurs


async def start_tcp_listeners(this_server):
    # Lazy way to avoid a circular import in an otherwise nice project structure
    from wcps_game.game.game_server import User

    try:
        tcp_server = await asyncio.start_server(
            lambda reader, writer: User(reader, writer, this_server),
            host=this_server.ip,
            port=this_server.port,
        )
        logging.info("TCP listener started.")
    except OSError:
        logging.error(f"Failed to bind to port {this_server.ip}:{this_server.port}")
        raise SystemExit("TCP listener failed. Server stopped.")

    await asyncio.gather(tcp_server.serve_forever())
