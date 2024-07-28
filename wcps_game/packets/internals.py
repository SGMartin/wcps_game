from wcps_core.constants import InternalKeys
from wcps_core.packets import OutPacket

class InternalPacketsIds:
    SERVERKEEPALIVE = 0x999

class GameServerDetails(OutPacket):
    def __init__(self):
        super().__init__(
        packet_id=0x1000,
        xor_key=InternalKeys.XOR_GAME_SEND
        )

        self.append("1") ## Error code
        self.append("0") ## Server ID
        self.append("Test ") ## Server name
        self.append("127.0.0.1")
        self.append(5340)
        self.append(0) ## type
        self.append(100) ## curr pop
        self.append(500) ## max pop