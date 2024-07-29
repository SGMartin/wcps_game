import asyncio
import logging

from typing import TYPE_CHECKING

from wcps_core.constants import Ports, ServerTypes
from wcps_core.packets import InPacket, Connection

if TYPE_CHECKING:
    from handlers.handler_list import get_handler_for_packet
    from packets.internals import GameServerDetails

class ClientXorKeys:
    SEND = 0x96
    RECEIVE = 0xC3

class GameServer:
    def __init__(self):
        self.name = "WCPS"
        self.ip = "127.0.0.1"
        self.port = Ports.GAME_CLIENT
        self.current_players = 0
        self.max_players = 0
        self.current_rooms = 0
        self.id = 0
        self.server_type = ServerTypes.ENTIRE

class User:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        ## network related tasks
        self.reader = reader
        self.writer = writer

        ## Send a connection packet to the client
        asyncio.create_task(self.send(Connection(xor_key=ClientXorKeys.SEND).build()))

        ## Start listening for client packets
        asyncio.create_task(self.listen())

    async def listen(self):
        while True:
            data = await self.reader.read(1024)
            if not data:
                await self.disconnect()
                break

            try:
                incoming_packet = InPacket(buffer=data, receptor=self, xor_key=ClientXorKeys.RECEIVE)
                if incoming_packet.decoded_buffer:
                    logging.info(f"IN:: {incoming_packet.decoded_buffer}")
                    handler = get_handler_for_packet(incoming_packet.packet_id)
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
