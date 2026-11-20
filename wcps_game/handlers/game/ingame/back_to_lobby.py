import asyncio

from wcps_core.constants import ErrorCodes as corerr

from wcps_game.game.constants import RoomStatus
from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.packet_list import PacketList


class BackToLobbyHandler(GameProcessHandler):
    async def handle(self):
        if self.room.state != RoomStatus.WAITING:
            return

        if self.player.state == RoomStatus.WAITING or self.player.back_to_lobby_pending:
            return

        # Same answer the generic path builds: the request echoed back to this player only
        answer = PacketFactory.create_packet(
            packet_id=PacketList.DO_GAME_PROCESS,
            blocks=[corerr.SUCCESS, self.room_slot, self.room.id, self.packet.blocks[2], self.sub_packet]
            + self.blocks,
        )

        if self.player.mission_requested:
            await self.room.back_to_lobby(self.player, answer)
        else:
            # The game ended while this client was loading: wait for its 402 first (#63)
            asyncio.create_task(self.room.back_to_lobby_after_mission(self.player, answer))
