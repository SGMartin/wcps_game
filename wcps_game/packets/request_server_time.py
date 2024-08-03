import datetime
import locale

from wcps_core.constants import ErrorCodes as corerr
from wcps_core.packets import OutPacket

from wcps_game.packets.error_codes import ServerTimeError
from wcps_game.packets.packet_list import PacketList, ClientXorKeys


class ServerTime(OutPacket):
    def __init__(self, error_code: ServerTimeError):
        super().__init__(packet_id=PacketList.REQUEST_SERVER_TIME, xor_key=ClientXorKeys.SEND)
        if error_code != corerr.SUCCESS:
            self.append(error_code)
        else:
            # get server time
            now = datetime.utcnow()
            # 0 offset dates
            month = now.month - 1
            year = now.year - 1900
            # get week
            locale.setlocale(locale.LC_TIME, "")
            week = now.isocalendar()[1]
            # build final date block
            date_string = now.strftime(
                "%S/%M/%H/%d") + f"/{month}/{year}/{week}/{now.timetuple().tm_yday}/0"

            self.append(corerr.SUCCESS)
            self.append(date_string)
