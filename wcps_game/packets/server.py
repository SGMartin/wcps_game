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


class PlayerAuthorization(OutPacket):
    class ErrorCodes(Enum):
        NormalProcedure = 73030     # Please log in using the normal procedure!
        InvalidPacket = 90100       # Invalid Packet.
        UnregisteredUser = 90101    # Unregistered User.
        AtLeast6Chars = 90102       # You must type at least 6 characters .
        NicknameToShort = 90103     # Nickname should be at least 6 charaters.
        IdInUseOtherServer = 90104  # Same ID is being used on the server.
        NotAccessible = 90105       # Server is not accessible.
        TrainingServer = 90106      # Trainee server is accesible until the rank of a private..
        ClanWarError = 90112        # You cannot participate in Clan War
        LackOfResponse = 91010      # Connection terminated because of lack of response for a while.
        ServerIsFull = 91020        # You cannot connect. Server is full.
        InfoReqInTrafic = 91030     # Info request are in traffic.
        AccountUpdateFailed = 91040 # Account update has failed.
        BadSynchronization = 91050  # User Info synchronization has failed.
        IdInUse = 92040             # That ID is currently being used.
        PremiumOnly = 98010         # Available to Premium users only.
        
    def __init__(self, error_code:ErrorCodes):
        super().__init__(
            packet_id=PacketList.Authorization,
            xor_key=ClientXorKeys.SEND
        )
        self.append(error_code.value)
