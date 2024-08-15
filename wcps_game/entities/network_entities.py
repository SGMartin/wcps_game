import asyncio
import logging

from wcps_core.packets import InPacket, Connection


class NetworkEntity:
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        xor_key_send,
        xor_key_receive,
    ):
        self.reader = reader
        self.writer = writer
        self.xor_key_send = xor_key_send
        self.xor_key_receive = xor_key_receive
        self.authorized = False
        self.session_id = -1

        self._connection = Connection(xor_key=self.xor_key_send).build()
        asyncio.create_task(self.send(self._connection))
        asyncio.create_task(self.listen())

    async def listen(self):
        while True:
            try:
                data = await self.reader.read(1024)
                if not data:
                    await self.disconnect()
                    break

                incoming_packet = InPacket(
                    buffer=data, receptor=self, xor_key=self.xor_key_receive
                )
                if incoming_packet.decoded_buffer:
                    if incoming_packet.packet_id != 25600:
                        logging.info(f"IN:: {incoming_packet.decoded_buffer}")
                    handler = self.get_handler_for_packet(incoming_packet.packet_id)
                    if handler:
                        asyncio.create_task(handler.handle(incoming_packet))
                    else:
                        logging.error(
                            f"Unknown handler for packet {incoming_packet.packet_id}"
                        )
                else:
                    logging.error(f"Cannot decrypt packet {incoming_packet}")
                    await self.disconnect()
                    break

            except ConnectionResetError as e:
                logging.error(f"Connection reset by peer: {e}")
                await self.disconnect()
                break
            except asyncio.CancelledError:
                logging.info("Task was cancelled")
                break
            except Exception as e:
                logging.exception(f"Unexpected error while processing packet: {e}")
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
        try:
            self.writer.close()
            await self.writer.wait_closed()  # Ensure the writer is closed properly
        except ConnectionResetError:
            # The connection has already been reset by the peer; no action needed
            logging.warning("Attempted to close already reset connection.")
        except Exception as e:
            logging.exception(f"Error during disconnection: {e}")

    def get_handler_for_packet(self, packet_id: int):
        raise NotImplementedError("Subclasses must implement this method.")
