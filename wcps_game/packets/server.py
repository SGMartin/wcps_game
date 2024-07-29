import locale
from datetime import datetime
from enum import Enum

from wcps_core.constants import ErrorCodes as er
from wcps_core.packets import OutPacket
from game.game_server import GameServer, User, ClientXorKeys

class PacketList():
    LeaveServer = 0x6000
    ServerTime = 0x6100
    Authorization = 0x6200
    Ping = 0x6400

class ServerTime(OutPacket):
    class ErrorCodes(Enum):
        FormatCPrank = 90010           #Format C Drive?
        DifferentClientVersion = 90020  #Client version is different. Please download the patch
        ReInstallWindowsPrank = 90030  #Reinstalling Windows.?

    def __init__(self, error_code:ErrorCodes):
        super().__init__(
        packet_id=PacketList.ServerTime,
        xor_key=ClientXorKeys.SEND
        )
        if error_code != er.SUCCESS:
            self.append(error_code.value)
        else:
            ## get server time
            self._now = datetime.utcnow()
            ## 0 offset dates
            self._month = self._now.month - 1
            self._year = self._now.year - 1900
            ## get week
            locale.setlocale(locale.LC_TIME, "")
            self._week = self._now.isocalendar()[1]
            ## build final date block
            self._date_string = self._now.strftime("%S/%M/%H/%d") + f"/{self._month}/{self._year}/{self._week}/{self._now.timetuple().tm_yday}/0"

            self.append(er.SUCCESS)
            self.append(self._date_string)


class LeaveServer(OutPacket):
    def __init(self):
        super().__init__(
            packet_id=PacketList.LeaveServer,
            xor_key=ClientXorKeys.SEND
        )
        self.append(er.SUCCESS)

