import time

from wcps_core.constants import InternalKeys, ErrorCodes
from wcps_core.packets import OutPacket
from wcps_core.packets import PacketList as corepackets

class GameServerDetails(OutPacket):
    def __init__(self):
        super().__init__(
        packet_id=corepackets.GameServerAuthentication,
        xor_key=InternalKeys.XOR_GAME_SEND
        )

        self.append(ErrorCodes.SUCCESS)
        self.append("0") ## Server ID
        self.append("Test ") ## Server name
        self.append("127.0.0.1")
        self.append(5340)
        self.append(0) ## type
        self.append(100) ## curr pop
        self.append(500) ## max pop

class GameServerStatus(OutPacket):
    def __init__(self):
        super().__init__(
        packet_id=corepackets.GameServerStatus,
        xor_key=InternalKeys.XOR_GAME_SEND
        )

        self.append(ErrorCodes.SUCCESS)
        self.append(int(time.time()))
        self.append(3600) ## current server pop
        self.append(50) ## current room pop
