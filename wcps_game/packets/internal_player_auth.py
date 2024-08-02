from wcps_core.constants import ErrorCodes, InternalKeys
from wcps_core.packets import OutPacket

from wcps_game.packets.packet_list import PacketList


class InternalPlayerAuthorization(OutPacket):
    def __init__(self, error_code: ErrorCodes, session_id: int, username: str, rights: int):
        super().__init__(
            packet_id=PacketList.ClientAuthentication,
            xor_key=InternalKeys.XOR_GAME_SEND
        )
        self.append(error_code)
        self.append(session_id)
        self.append(username)
        self.append(rights)
