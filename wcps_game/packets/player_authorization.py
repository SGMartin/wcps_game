from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_core.constants import ErrorCodes as er
from wcps_core.packets import OutPacket

from wcps_game.game.constants import get_level_for_exp
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
            self.append(u.equipment.get_slot_string())  # T/F = Slot enabled/disabled: slots: 5 -8
            self.append("DA02,DB01,DF01,DR01,^,^,^,^")  # engineer current loadout
            self.append("DA02,DB01,DF01,DQ01,^,^,^,^")  # medic current loadout
            self.append("DA02,DB01,DG05,DN01,^,^,^,^")  # sniper current loadout
            self.append("DA02,DB01,DC04,DN01,DH02,^,^,^")  # assault current loadout
            self.append("DA02,DB01,DJ01,DL01,^,^,^,^")  # heavy trooper current loadout

            # nventory (max 31)
            item_list = ""
            for i in range(32):
                if i == 0:
                    item_list = "^"
                else:
                    item_list += ",^"

            item_list_2 = "DE01-3-0-24080408-0-0-0-0-0-0-0,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^"
            self.append(item_list_2)
            self.fill(0, 2)  # ?
