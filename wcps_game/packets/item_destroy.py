from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_core.constants import ErrorCodes as corerr
from wcps_core.packets import OutPacket

from wcps_game.game.constants import Classes
from wcps_game.packets.packet_list import ClientXorKeys, PacketList


class ItemDestroy(OutPacket):
    """Answer to DO_ITEM_DESTROY. On success the client reloads its inventory, slot states and the five
    loadouts from it, and shows m_itemdelete_2; on anything else it shows m_itemdelete_4."""

    def __init__(self, error_code: int, user: "User" = None, item_code: str = ""):
        super().__init__(packet_id=PacketList.DO_ITEM_DESTROY, xor_key=ClientXorKeys.SEND)

        if error_code != corerr.SUCCESS or user is None:
            self.append(error_code)
            return

        self.append(corerr.SUCCESS)
        self.append(item_code)
        self.append(user.inventory.inventory_string)
        self.append(user.inventory.get_slot_string())
        for branch in (Classes.ENGINEER, Classes.MEDIC, Classes.SNIPER, Classes.ASSAULT, Classes.HEAVY):
            self.append(user.inventory.equipment.loadout[branch])
