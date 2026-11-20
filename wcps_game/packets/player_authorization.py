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
            packet_id=PacketList.DO_JOIN_SERV,
            xor_key=ClientXorKeys.SEND
        )
        if error_code != er.SUCCESS or not u:
            self.append(error_code)
        else:
            # basic user data
            self.append(er.SUCCESS)
            self.append("Gameserver1")
            self.append(u.session_id)   # session id
            self.append(u.session_id)  # user id? Used to be internal id
            self.append(u.session_id)   # session.id
            self.append(u.displayname)  # displayname
            # clan blocks: id, name (read as a string here), two more ints (PF23 0x5fbf60)
            self.fill(-1, 4)

            # user stats
            self.append(u.premium)       # premium state
            self.append(0)       # portal logo: 1..8 draws a sprite of texCPLOGO, 0 = none (PF23 0x541a5d)
            self.append(0)       # stored, no client reader found
            self.append(get_level_for_exp(u.xp))      # player level
            self.append(u.xp)  # exp
            self.append(0)       # stored, no client reader found
            self.append(0)       # stored, no client reader found
            self.append(u.money)   # money
            self.append(u.stats.kills)      # kills
            self.append(u.stats.deaths)      # deaths
            self.fill(0, 5)      # stored, no client reader found (a client path sets the 3rd to 1)

            # SLOT STATE and loadouts
            self.append(u.inventory.get_slot_string())  # T/F = Slots 5-8 enabled/disabled
            self.append(u.inventory.equipment.loadout[Classes.ENGINEER])  # engineer current loadout
            self.append(u.inventory.equipment.loadout[Classes.MEDIC])  # medic current loadout
            self.append(u.inventory.equipment.loadout[Classes.SNIPER])  # sniper current loadout
            self.append(u.inventory.equipment.loadout[Classes.ASSAULT])  # assault current loadout
            self.append(u.inventory.equipment.loadout[Classes.HEAVY])  # heavy current loadout

            # inventory (max 31)
            self.append(u.inventory.inventory_string)
            # The client reads only the first one (no reader found for it) and ignores the second
            # (PF23 0x5fbf60). Two more ints would come first, behind a flag (+0x4e434) the client
            # never sets.
            self.fill(0, 2)
