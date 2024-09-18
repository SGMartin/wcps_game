from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_core.constants import ErrorCodes as corerr
from wcps_core.packets import OutPacket

from wcps_game.game.constants import ItemAction
from wcps_game.packets.packet_list import ClientXorKeys, PacketList
from wcps_game.packets.error_codes import ItemShopError


class ItemShop(OutPacket):
    def __init__(self, error_code: ItemShopError, user: "User" = None):
        super().__init__(packet_id=PacketList.DO_ITEM_PROCESS, xor_key=ClientXorKeys.SEND)

        if error_code != corerr.SUCCESS or not user:
            self.append(error_code)
        else:
            self.append(corerr.SUCCESS)
            self.append(ItemAction.BUY)
            self.append(-1)  # ??
            self.append(3)  # ? client version as reported in request time? buy type??
            self.append(len(user.inventory.item_list))
            self.append(user.inventory.inventory_string)
            self.append(user.money)
            self.append(user.inventory.get_slot_string())
