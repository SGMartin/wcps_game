from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_core.constants import ErrorCodes
from wcps_core.packets import OutPacket

from wcps_game.game.constants import Classes
from wcps_game.packets.packet_list import PacketList, ClientXorKeys


class UpdateInventory(OutPacket):
    def __init__(self, user: "User"):
        super().__init__(
            packet_id=PacketList.UPDATE_INVENTORY,
            xor_key=ClientXorKeys.SEND
        )
        self.append(ErrorCodes.SUCCESS)
        self.append(user.inventory.get_slot_string())  # slot status
        self.append(user.inventory.equipment.loadout[Classes.ENGINEER])  # engineer current loadout
        self.append(user.inventory.equipment.loadout[Classes.MEDIC])  # medic current loadout
        self.append(user.inventory.equipment.loadout[Classes.SNIPER])  # sniper current loadout
        self.append(user.inventory.equipment.loadout[Classes.ASSAULT])  # assault current loadout
        self.append(user.inventory.equipment.loadout[Classes.HEAVY])  # heavy current loadout
        self.append(user.inventory.inventory_string)

        expired_items = user.inventory.expired_items

        self.append(len(expired_items))
        for item in expired_items:
            self.append(item.item_code)
