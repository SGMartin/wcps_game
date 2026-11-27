import asyncio
import logging

from wcps_core.packets import PacketBuffer, Connection

from wcps_game.packets.packet_list import PacketList


class NetworkEntity:
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        xor_key_send,
        xor_key_receive,
        send_greeting: bool = True,
    ):
        self.reader = reader
        self.writer = writer
        self.xor_key_send = xor_key_send
        self.xor_key_receive = xor_key_receive
        self.authorized = False
        self.session_id = -1
        # Set the first time disconnect() runs: the cleanup happens once, and nothing is sent after it
        self.disconnected = False

        # The side that accepts the connection greets (0x1200); the one that opens it does not
        if send_greeting:
            self._connection = Connection(xor_key=self.xor_key_send).build()
            asyncio.create_task(self.send(self._connection))
        asyncio.create_task(self.listen())

    async def listen(self):
        try:
            while not self.disconnected:
                data = await self.reader.read(1024)
                if not data:  # end of stream: the peer is gone, or drop() closed the connection
                    break

                incoming_packets = PacketBuffer(
                    buffer=data, receptor=self, xor_key=self.xor_key_receive
                )
                if not incoming_packets.decoded_buffer:
                    logging.error(f"Cannot decrypt packet {incoming_packets}")
                    break

                for packet in incoming_packets.packet_stack:

                    if packet.packet_id != PacketList.DO_KEEPALIVE:  # one per user every ping round
                        logging.info(f"IN:: {packet.decoded_buffer}")

                    handler = self.get_handler_for_packet(packet.packet_id)
                    if handler:
                        asyncio.create_task(handler.handle(packet))
                    else:
                        logging.error(
                            f"Unknown handler for packet {packet.packet_id}"
                        )

        except asyncio.CancelledError:
            logging.info("Task was cancelled")
            raise
        except ConnectionResetError as e:
            logging.warning(f"Connection reset by peer: {e}")
        except Exception as e:
            logging.exception(f"Unexpected error while processing packet: {e}")

        # The only place where a lost connection is cleaned up, in this entity's own task
        await self.disconnect()

    async def send(self, buffer):
        writer = self.writer
        if self.disconnected or writer is None or writer.is_closing():
            return

        try:
            writer.write(buffer)
            await writer.drain()
        except Exception as e:
            logging.warning(f"Error sending packet, dropping the connection: {e}")
            self.drop()

    def drop(self):
        """Close the connection without cleaning up here.

        The send may come from another entity's task (a room broadcast) that holds a room lock;
        disconnecting from there would wait for that same lock forever. Closing the transport ends
        listen(), which then runs disconnect() in this entity's own task.
        """
        writer = self.writer
        if writer is not None and not writer.is_closing():
            writer.close()

    async def disconnect(self):
        if self.disconnected:
            return
        self.disconnected = True

        try:
            await self.on_disconnect()
        except Exception as e:
            logging.exception(f"Error cleaning up after disconnection: {e}")

        await self.close_connection()

    async def on_disconnect(self):
        """What to clean up when the connection ends. Runs once, before the connection is closed."""
        pass

    async def close_connection(self):
        writer = self.writer
        if writer is None:
            return

        try:
            writer.close()
            await writer.wait_closed()
        except (ConnectionResetError, BrokenPipeError):
            pass  # already closed by the peer
        except Exception as e:
            logging.warning(f"Error closing the connection: {e}")

    def get_handler_for_packet(self, packet_id: int):
        raise NotImplementedError("Subclasses must implement this method.")
