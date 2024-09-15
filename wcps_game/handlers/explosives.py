from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_game.game.constants import Classes, GameMode, RoomStatus
from wcps_game.handlers.packet_handler import PacketHandler
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory


class ExplosivesHandler(PacketHandler):
    async def process(self, user: "User") -> None:

        if not user.authorized:
            return

        if user.room is None:
            return

        if user.room.state != RoomStatus.PLAYING:
            return

        # BOMB
        # b'18452927 29984 0 0 0 59 1 3660.0313 93.4193 2526.1655 88.4800 192.3299 212.5570 \n')
        # TMA
        # b'18573441 29984 0 0 2 49 0 4517.7847 93.1953 3442.6011 -6.0064 -43.2490 -296.8054 \n')

        player_slot_id = int(self.get_block(0))
        is_exploding = bool(int(self.get_block(1)))
        action_type = int(self.get_block(2))

        # Unused atm
        item_id = int(self.get_block(3))
        # bomb_site = int(self.get_block(4))

        # Check if we can get the player id
        this_player = user.room.players.get(player_slot_id)

        if this_player is None or this_player.user != user:
            return

        if this_player.health <= 0 or not this_player.alive:
            return

        # Actual CQC bomb
        if action_type == 0:
            # TODO: validate C4 and items
            # print(f"Item id is {item_id}")

            if user.room.game_mode != GameMode.EXPLOSIVE:
                return

            should_answer = await user.room.current_game_mode.handle_explosives(player=this_player)

            if should_answer:
                explosives = PacketFactory.create_packet(
                    packet_id=PacketList.DO_BOMB_PROCESS,
                    blocks=self.in_packet.blocks
                )

                await user.room.send(explosives.build())

        # TMA bomb placement
        # TODO: check if TMA id is 59
        elif action_type == 2 and not is_exploding and this_player.branch == Classes.HEAVY:
            item_id = await user.room.add_item(
                owner=this_player,
                code=item_id  # it's using numerical ids instead of item codes as with medickits
            )
            this_player.items_planted += 1

            # Send back the packet as is
            blocks_to_send = self.in_packet.blocks

            explosives = PacketFactory.create_packet(
                packet_id=PacketList.DO_BOMB_PROCESS,
                blocks=blocks_to_send
            )

            await user.room.send(explosives.build())
