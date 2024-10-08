import asyncio
import logging

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_game.handlers.packet_handler import PacketHandler
from wcps_game.handlers.game_handler_factory import get_subhandler_for_packet


class GameProcessHandler(PacketHandler):
    async def process(self, user: "User") -> None:

        if not user.authorized or user.room is None:
            return

        # bytearray(b'32565270 30000 0 0 2 51 1 0 13 0 0 0 0 0 0 0 \n')
        room_slot = int(self.get_block(0))
        room_id = int(self.get_block(1))
        packet_subtype = int(self.get_block(3))

        if room_slot >= user.room.max_players or room_id != user.room.id:
            logging.info(f"Unknown packet recipient: {self.block}")
            return

        # Try to find the subpacket handler for this
        handler = get_subhandler_for_packet(subpacket_id=packet_subtype)
        if handler is None:
            logging.info(f"Unknown subpacket handler for {packet_subtype}")
        else:
            asyncio.create_task(handler.process(user, in_packet=self.in_packet))
