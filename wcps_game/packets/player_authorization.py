from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_core.constants import ErrorCodes as er
from wcps_core.packets import OutPacket

from wcps_game.game.constants import get_level_for_exp, Classes
from wcps_game.packets.error_codes import PlayerAuthorizationError
from wcps_game.packets.packet_list import ClientXorKeys, PacketList


class PlayerAuthorization(OutPacket):
    def __init__(self, error_code: PlayerAuthorizationError, u: "User" = None):
        super().__init__(
            packet_id=PacketList.PLAYER_AUTHORIZATION,
            xor_key=ClientXorKeys.SEND
        )
        if error_code != er.SUCCESS or not u:
            self.append(error_code)
        else:
            # basic user data
            self.append(er.SUCCESS)
            self.append("Gameserver1")
            self.append(u.session_id)   # session id
            self.append(u.internal_id)  # user id?
            self.append(u.session_id)   # session.id
            self.append(u.displayname)  # displayname
            # clan blocks
            self.fill(-1, 4)

            # user stats
            self.append(u.premium)       # premium state
            self.append(0)       # ?
            self.append(0)       # ?
            self.append(get_level_for_exp(u.xp))      # player level
            self.append(u.xp)  # exp
            self.append(0)       # ?
            self.append(0)       # ?
            self.append(u.money)   # money
            self.append(u.stats.kills)      # kills
            self.append(u.stats.deaths)      # deaths
            self.fill(0, 5)      # ????

            # SLOT STATE and loadouts
            self.append(u.inventory.equipment.get_slot_string())  # T/F = Slots 5-8 enabled/disabled
            self.append(u.inventory.equipment.loadout[Classes.ENGINEER])  # engineer current loadout
            self.append(u.inventory.equipment.loadout[Classes.MEDIC])  # medic current loadout
            self.append(u.inventory.equipment.loadout[Classes.SNIPER])  # sniper current loadout
            self.append(u.inventory.equipment.loadout[Classes.ASSAULT])  # assault current loadout
            self.append(u.inventory.equipment.loadout[Classes.HEAVY])  # heavy current loadout

            # inventory (max 31)
            self.append(u.inventory.inventory_string)
            self.fill(0, 2)  # ?
