from enum import Enum
from wcps_core import constants

from wcps_core.packets import OutPacket
from wcps_core import constants


class ClientXorKeys:
    Send = 0x96
    Recieve = 0xC3


class GameServerAuthentication(OutPacket):
    def __init__(self):
        super().__init__(
        packet_id=0x1000,
        xor_key=constants.InternalKeys.XOR_GAME_SEND
        )

        self.append("1") ## Error code
        self.append("Test ") ## Server name
        self.append("IP")
        self.append("Ports")
        self.append("ServerClass")