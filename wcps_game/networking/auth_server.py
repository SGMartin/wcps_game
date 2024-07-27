import asyncio
import logging

from wcps_core.constants import ServerTypes, InternalKeys
from wcps_core.packets import InPacket, OutPacket, Connection
from networking.packets import GameServerAuthentication

import networking.handlers

class AuthenticationServer:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.address, self.port = reader._transport.get_extra_info("peername")
        self.reader = reader
        self.writer = writer

        # Start the listen loop
        asyncio.create_task(self.listen())
    
    async def listen(self):
        while True:
            # Read a line of data from the client
            data = await self.reader.read(1024)

            if not data:
                self.disconnect()
                break
            else:
                incoming_packet = InPacket(
                    buffer=data, receptor=self, xor_key=self.xor_key_recieve
                )
                if incoming_packet.decoded_buffer:
                    print(f"IN:: {incoming_packet.decoded_buffer}")
                    handler = networking.handlers.get_handler_for_packet(
                        incoming_packet.packet_id
                    )
                    if handler:
                        asyncio.create_task(handler.handle(incoming_packet))

    async def send(self, buffer):
        try:
            self.writer.write(buffer)
            await self.writer.drain()
        except Exception as e:
            print(f"Error sending packet: {e}")
            self.disconnect()

    def disconnect(self):
        self.writer.close()
        if self.authorized:
            sessions.Remove(self)


class AuthenticationClient:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.reader = None
        self.writer = None
        self.max_retries = 5

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

    async def receive_message(self):
        if self.reader is None:
            raise ConnectionError("Client is not connected. Call 'connect' first.")

        while True:
            # Read a line of data from the client
            data = await self.reader.read(1024)

            if not data:
                await self.disconnect()
                break
            else:
                incoming_packet = InPacket(
                    buffer=data, receptor=self, xor_key=InternalKeys.XOR_AUTH_SEND
                )
                if incoming_packet.decoded_buffer:
                    print(f"IN:: {incoming_packet.decoded_buffer}")
                    handler = networking.handlers.get_handler_for_packet(
                        incoming_packet.packet_id
                    )
                    if handler:
                        asyncio.create_task(handler.handle(incoming_packet))
                    else:
                        print(f"Unknown handler for packet {incoming_packet.packet_id}")


    async def disconnect(self):
        if self.writer:
            logging.info('Closing the connection')
            self.writer.close()
            await self.writer.wait_closed()
            self.reader = None
            self.writer = None


    async def run(self, message: str):
        await self.connect()
        # Handle incoming messages
        try:
            while True:
                response = await self.receive_message()
                if response:
                    # Process the received message here
                    logging.info(f'Received from server: {response}')
                else:
                    break
        finally:
            await self.disconnect()