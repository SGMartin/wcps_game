from wcps_core.constants import ErrorCodes as correrr
from wcps_core.packets import OutPacket

from wcps_game.packets.error_codes import EquipmentError
from wcps_game.packets.packet_list import ClientXorKeys, PacketList


class Equipment(OutPacket):
    def __init__(self, error_code: EquipmentError, target_class: int, new_loadout: str):
        super().__init__(
            packet_id=PacketList.EQUIPMENT,
            xor_key=ClientXorKeys.SEND
        )
        if error_code != correrr.SUCCESS:
            self.append(error_code)
        else:
            self.append(correrr.SUCCESS)
            self.append(target_class)
            self.append(new_loadout)
