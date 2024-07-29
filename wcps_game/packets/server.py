from datetime import datetime
from enum import Enum

from wcps_core.constants import ErrorCodes as er
from wcps_core.packets import OutPacket
from game.game_server import GameServer, User, ClientXorKeys

class PacketList():
    ServerTime = 0x6100

class ServerTime(OutPacket):
    class ErrorCodes(Enum):
        FormatCPrank = 90010           #Format C Drive?
        DifferentClientVersion = 90020  #Client version is different. Please download the patch
        ReInstallWindowsPrank = 90030  #Reinstalling Windows.?

    def __init__(self, this_server:GameServer, error_code:ErrorCodes):
        super().__init__(
        packet_id=corepackets.GameServerAuthentication,
        xor_key=ClientXorKeys.SEND
        )
        if error_code != er.SUCCESS:
            self.append(error_code.value)
        else:
            ## get server time
            self._now = datetime.utcnow()
            ## 0 offset dates
            self._month = now.month - 1
            self._year = now.year - 1900
            ## get week
            self._locale.setlocale(locale.LC_TIME, "")
            self._week = dt.isocalendar()[1]
            ## build final date block
            self._date_string = now.strftime("%S/%M/%H/%d") + f"/{self._month}/{self._year}/{self._week}/{self._now.timetuple().tm_yday}/0"

            self.append(er.SUCCESS)
            self.append(self._date_string)




