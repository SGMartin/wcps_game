import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_core.constants import ErrorCodes as corerr

from wcps_game.game.constants import MAX_CLASSES, RoomStatus
from wcps_game.handlers.packet_handler import PacketHandler
from wcps_game.packets.error_codes import ItemDestroyError
from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.packet_list import PacketList


class ItemDestroyHandler(PacketHandler):
    """DO_ITEM_DESTROY: the player deletes an item from the inventory, after the client's yes/no box.

    The client sends the item code and its index among the account's items in use (or -1). The item is
    looked up by code, so the index is not needed. Default weapons are not in the inventory, so they
    cannot be deleted.
    """

    async def process(self, user: "User") -> None:
        if not user.authorized:
            return

        item_code = self.get_block(0)

        # The inventory is not open during a match
        in_match = user.room is not None and user.room.state == RoomStatus.PLAYING

        if in_match or not user.inventory.has_item(item_code):
            logging.warning(f"{user.username} cannot delete {item_code}")
            await self.answer(user, ItemDestroyError.FAILED)
            return

        # Take it off every branch first: a deleted item must not stay in a loadout
        equipment = user.inventory.equipment
        for branch in range(MAX_CLASSES):
            slot = equipment.is_equipped_in_class(target_class=branch, weapon=item_code)
            if slot is not None and slot != -1:
                await equipment.remove_item_from_slot(target_class=branch, target_slot=slot)

        await user.inventory.remove_item(item_to_remove=item_code)
        logging.info(f"{user.username} deleted {item_code}")

        await self.answer(user, corerr.SUCCESS, item_code)

    async def answer(self, user: "User", error_code: int, item_code: str = ""):
        packet = PacketFactory.create_packet(
            packet_id=PacketList.DO_ITEM_DESTROY,
            error_code=error_code,
            user=user,
            item_code=item_code,
        )
        await user.send(packet.build())
