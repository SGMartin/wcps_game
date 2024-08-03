import asyncio
import struct
import logging
from typing import Tuple, Optional


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
                self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
                logging.info(f'Connected to authentication server at {self.ip}:{self.port}')
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
    # Define the XOR keys for UDP
    XOR_SEND_KEY = 0xC3
    XOR_RECEIVE_KEY = 0x96

    def __init__(self, port: int):
        self.port = port
        self.transport: Optional[asyncio.DatagramTransport] = None
        self.loop = asyncio.get_event_loop()

    async def start(self):
        """Start the UDP listener on the specified port."""
        loop = asyncio.get_event_loop()
        self.transport, _ = await loop.create_datagram_endpoint(
            lambda: UDPProtocol(self), local_addr=("0.0.0.0", self.port)
        )
        logging.info(f"UDP server listening on port {self.port}")

    def handle_packet(self, packet: bytes, addr: Tuple[str, int]):
        """Handle incoming packets."""
        packet = bytearray(packet)  # Convert to bytearray for mutable operations
        type_ = self.to_ushort(packet, 0)
        session_id = self.to_ushort(packet, 4)
        # Skip user manager code, handle logic with type and session_id here
        logging.info(f"IN:: UDP packet of type {type_} with session ID {session_id}")

        if type_ == 0x1001:  # Initial packet
            self.write_ushort(self.port + 1, packet, 4)
            self.transport.sendto(packet, addr)
        elif type_ == 0x1010:  # UDP Ping packet
            if packet[14] == 0x21:
                # Example for UDP Ping packet handling
                response = bytearray(65)
                response[17] = 0x41
                response[-1] = 0x11
                self.write_ushort(session_id, response, 4)
                # Write endpoints to response
                # Example: self.write_ip_endpoint(remote_endp, response, 32)
                # Example: self.write_ip_endpoint(local_endp, response, 50)
                self.transport.sendto(response, addr)
            elif packet[14] in {0x10, 0x30, 0x31, 0x32, 0x34}:
                # Handle additional sub-packet types
                pass
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
        # XOR the bytes with the XOR key
        for i in range(offset, offset + 6):
            data[i] ^= XOR_SEND_KEY
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
        # Convert IP address and port to byte arrays
        port_bytes = struct.pack(">H", port)
        ip_bytes = struct.pack(
            ">I",
            int(ip_address.split(".")[0]) << 24
            | int(ip_address.split(".")[1]) << 16
            | int(ip_address.split(".")[2]) << 8
            | int(ip_address.split(".")[3]),
        )

        # Combine port and IP address
        value = port_bytes + ip_bytes

        # XOR with the XOR key
        value = bytearray(b ^ XOR_RECEIVE_KEY for b in value)

        # Write to data array
        data[offset: offset + 6] = value
        return data

    def ip_to_int(self, ip_address: str) -> int:
        """Convert IP address to an integer."""
        parts = map(int, ip_address.split("."))
        return (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]


class UDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, listener: UDPListener):
        self.listener = listener

    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        """Called when a datagram is received."""
        self.listener.handle_packet(data, addr)

    def error_received(self, exc: Exception):
        """Handle any errors."""
        logging.error(f"Error received: {exc}")
        if self.listener.transport:
            self.listener.transport.close()
