from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room

from wcps_core.constants import ErrorCodes as corerr
from wcps_core.packets import OutPacket
from wcps_game.packets.packet_list import ClientXorKeys, PacketList


class ScoreBoard(OutPacket):
    def __init__(self, room: "Room"):
        super().__init__(packet_id=PacketList.DO_GAME_SCORE, xor_key=ClientXorKeys.SEND)

        self.append(corerr.SUCCESS)

        self.append(room.current_game_mode.current_round_derbaran())
        self.append(room.current_game_mode.current_round_niu())
        self.append(room.current_game_mode.scoreboard_derbaran())
        self.append(room.current_game_mode.scoreboard_niu())

        players = room.get_all_players()
        self.append(len(players))
        for player in players:
            self.append(player.id)
            self.append(player.kills)
            self.append(player.deaths)
            self.append(player.flags_taken)
            self.append(player.assists + player.points)  # Odd WR stuff
            self.append(0)  # Everything you set here is set as negative
