from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_core.packets import OutPacket
from wcps_core.constants import ErrorCodes as corerr

from wcps_game.game.constants import ChatChannel
from wcps_game.packets.packet_list import ClientXorKeys, PacketList


class Chat(OutPacket):
    def __init__(
        self,
        error_code: corerr,
        receiver_id: int,
        receiver_username: str,
        user: "User",
        chat_type: ChatChannel = -1,
        message: str = ""
    ):

        super().__init__(
            packet_id=PacketList.CHAT,
            xor_key=ClientXorKeys.SEND
        )

        if error_code != corerr.SUCCESS:
            self.append(error_code)
            self.append(f"{receiver_username} ")
        else:
            self.append(corerr.SUCCESS)
            self.append(user.session_id)
            self.append(user.displayname)
            self.append(chat_type)
            self.append(receiver_id)
            self.append(receiver_username)
            self.append(message_translator(message))


def message_translator(human_readable: str):
    # Define the special characters
    delimiter = ">>" + chr(0x1D)
    space_char = chr(0x20)
    control_char = chr(0x1D)

    # Insert the delimiter at the beginning of the message
    coded_message = delimiter + human_readable

    # Replace spaces with the control character
    coded_message = coded_message.replace(space_char, control_char)
    return coded_message
