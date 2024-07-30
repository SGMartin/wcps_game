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
        
    def __init__(self, error_code:ErrorCodes, u: User):
        super().__init__(
            packet_id=PacketList.Authorization,
            xor_key=ClientXorKeys.SEND
        )
        if error_code != er.SUCCESS or not u:
            self.append(error_code.value)
        else:
            ## basic user data
            self.append(er.SUCCESS)
            self.append("Gameserver1")
            self.append(u.session_id) ## session id
            self.append(1) ## user id?
            self.append(u.session_id) ## session.id
            self.append("DarkRaptor") ##displayname
            ## clan blocks
            self.fill(-1, 4)

            ## user stats
            self.append(3) ## premium state
            self.append(0) # ?
            self.append(0) # ?
            self.append(28) ## player level
            self.append(441500) # exp
            self.append(0) #?
            self.append(0) #?
            self.append(50000) # money
            self.append(20) #kills
            self.append(10) # deaths
            self.fill(0, 5) #????

            ## SLOT STATE and loadouts
            ## Append(u.Inventory.SlotState); // T = Slot Enabled, F = Slot disabled.
            self.append("F,F,F,F") ## slots
            ## engineer, medic, sniper, assault and heavy loadout
            # DA02,DB01,DF01,DR01,^,^,^,^
            # DA02,DB01,DF01,DQ01,^,^,^,^
            self.append("DA02,DB01,DF01,DR01,^,^,^,^")
            self.append("DA02,DB01,DF01,DQ01,^,^,^,^")
            self.append("DA02,DB01,DG05,DN01,^,^,^,^")
            self.append("DA02,DB01,DC04,DN01,^,^,^,^")
            self.append("DA02,DB01,DJ01,DL01,^,^,^,^")

            ## Inventory (max 31)
            item_list = ""
            for i in range(32):
                if i == 0:
                    item_list = "^"
                else:
                    item_list += ",^"

            item_list_2 = "^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^,^"
            self.append(item_list_2)
            self.fill(0, 2) ## ???

class Ping(OutPacket):
    def __init__(self, error_code, u: User):
        super().__init__(
            packet_id=PacketList.Ping,
            xor_key=ClientXorKeys.SEND
        )
        self.append(5000) # ping frequency
        self.append(0) # ping
        self.append(175) # -1 = no event, 175 = winter holidays
        self.append(100) # event duration
        self.append(0) # 3 exp weekend, 4 exp event, 0 = none
        self.append(1) # exp rate
        self.append(1) # dinar rate
        self.append(10000) # premium time in seconds -1 = no premium, 