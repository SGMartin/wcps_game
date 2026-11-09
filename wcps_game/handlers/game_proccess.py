import asyncio
import logging

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_game.handlers.packet_handler import PacketHandler
from wcps_game.handlers.game_handler_factory import get_subhandler_for_packet
from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.packet_list import PacketList


class GameProcessHandler(PacketHandler):
    async def process(self, user: "User") -> None:

        if not user.authorized or user.room is None:
            return

        # bytearray(b'32565270 30000 0 0 2 51 1 0 13 0 0 0 0 0 0 0 \n')
        room_slot = int(self.get_block(0))
        room_id = int(self.get_block(1))
        packet_subtype = int(self.get_block(3))

        is_spectator = user.room.is_spectator(user) and room_slot == user.room_slot

        if (room_slot >= user.room.max_players and not is_spectator) or room_id != user.room.id:
            logging.info(f"Unknown packet recipient: {self.in_packet.blocks}")
            return

        if is_spectator:
            await self.handle_spectator(user, packet_subtype)
            return

        # Try to find the subpacket handler for this
        handler = get_subhandler_for_packet(subpacket_id=packet_subtype)
        if handler is None:
            logging.info(f"Unknown subpacket handler for {packet_subtype}")
        else:
            asyncio.create_task(handler.process(user, in_packet=self.in_packet))

    async def handle_spectator(self, user: "User", packet_subtype: int) -> None:
        """Spectators are not Players, so the regular subhandlers cannot serve them.

        After loading the map the spectator client sends DO_REQUEST_MISSION (402) like a
        player does. Answer it only to the spectator with the map data. Unlike players it
        does NOT get DO_GO: in testing, DO_GO made the client leave the spectator view
        (players vanished from the minimap and the camera locked).
        Everything else is ignored for now.
        """
        if packet_subtype != PacketList.DO_REQUEST_MISSION:
            logging.info(f"Ignoring subpacket {packet_subtype} from spectator {user.displayname}")
            return

        room = user.room

        map_data = PacketFactory.create_packet(packet_id=PacketList.DO_GDATA_INFO, room=room)
        players_status = PacketFactory.create_packet(
            packet_id=PacketList.DO_GAME_UPDATE_DATA, room=room
        )
        await user.send(map_data.build())
        await user.send(players_status.build())
