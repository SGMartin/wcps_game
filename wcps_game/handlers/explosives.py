from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_game.game.constants import Classes, RoomStatus
from wcps_game.handlers.packet_handler import PacketHandler


class ExplosivesHandler(PacketHandler):
    async def process(self, user: "User") -> None:

        if not user.authorized:
            return

        if user.room is None:
            return

        if user.room.state != RoomStatus.PLAYING:
            return

        # TODO: take a look at the actual packet for references
        player_slot_id = int(self.get_block(0))
        is_exploding = bool(int(self.get_block(1)))
        action_type = int(self.get_block(2))
        item_id = int(self.get_block(3))

        # Check if we can get the player id
        this_player = user.room.players.get(player_slot_id)

        if this_player is None or this_player.user == user:
            return

        if action_type == 2 and not is_exploding and this_player.branch == Classes.HEAVY:
            print("PACKET HERE")
            pass
