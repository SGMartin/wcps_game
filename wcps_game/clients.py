import asyncio
import logging

import wcps_core.constants
import wcps_core.packets

from handlers.packet_handler import get_handler_for_packet

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
            await self.reconnect()

    async def listen(self):
        if self.reader is None:
            raise ConnectionError("Client is not connected. Call 'connect' first.")

        while True:
            try:
                data = await self.reader.read(1024)
                if not data:
                    await self.disconnect()
                    await self.reconnect()  # Attempt to reconnect
                    continue
                else:
                    incoming_packet = wcps_core.packets.InPacket(
                        buffer=data, 
                        receptor=self,
                        xor_key=wcps_core.constants.InternalKeys.XOR_AUTH_SEND
                    )
                    if incoming_packet.decoded_buffer:
                        print(f"IN:: {incoming_packet.decoded_buffer}")
                        handler = get_handler_for_packet(incoming_packet.packet_id)
                        if handler:
                            asyncio.create_task(handler.handle(incoming_packet))
                        else:
                            print(f"Unknown handler for packet {incoming_packet.packet_id}")
            except Exception as e:
                logging.error(f"Error during listening: {e}")
                await self.disconnect()
                await self.reconnect()

    async def disconnect(self):
        if self.writer:
            logging.info('Closing the connection')
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
