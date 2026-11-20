import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_core.constants import ErrorCodes as corerr
from wcps_core.packets import OutPacket

from wcps_game.game.constants import ItemAction
from wcps_game.packets.packet_list import ClientXorKeys, PacketList


class UsePXItem(OutPacket):
    def __init__(self, error_code: corerr, user: "User" = None, item_px: str = ""):
        super().__init__(packet_id=PacketList.DO_NCASH_PROCESS, xor_key=ClientXorKeys.SEND)

        if error_code != corerr.SUCCESS or not user or not item_px:
            self.append(error_code)
        else:
            self.append(ItemAction.USE)
            self.append(1)  # result: the client only handles the packet if it is 1
            self.append(item_px)
            self.append(user.inventory.inventory_string)
            if item_px == "CB03":  # Reset K/D ratio
                self.append(user.inventory.get_slot_string())
                # Not read: for CB03 the client reads nothing after the slots and zeroes K/D itself
                self.append(0)
                self.append(0)
                self.append(user.money)
            elif item_px == "CB01":  # Change NICKNAME TODO Research this. Not in PF20 default
                self.append(user.inventory.get_slot_string())
                self.append("notdone")  # the client copies this into its own nickname
            else:
                logging.error(f"Unknown item passed to packet {item_px}")
