from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_game.game.constants import RoomStatus
from wcps_game.handlers.packet_handler import PacketHandler
from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.packet_list import PacketList


class ScoreBoardHandler(PacketHandler):
    async def process(self, user: "User") -> None:

        if not user.authorized:
            return

        if user.room is None:
            return

        if user.room.state != RoomStatus.PLAYING:
            return

        score_board = PacketFactory.create_packet(
            packet_id=PacketList.DO_GAME_SCORE,
            room=user.room
        )
        await user.send(score_board.build())
