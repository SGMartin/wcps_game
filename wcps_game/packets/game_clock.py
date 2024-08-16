from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room

from wcps_core.packets import OutPacket

from wcps_game.packets.packet_list import PacketList, ClientXorKeys


class GameUpdateClock(OutPacket):
    def __init__(self, room: "Room"):
        super().__init__(
            packet_id=PacketList.DO_GAME_UPDATE_CLOCK,
            xor_key=ClientXorKeys.SEND
        )

        self.append(room.up_ticks)  # Spawn counter
        self.append(room.down_ticks)  # Time left
        self.append(room.current_game_mode.current_round_derbaran())
        self.append(room.current_game_mode.current_round_niu())
        self.append(room.current_game_mode.scoreboard_derbaran())
        self.append(room.current_game_mode.scoreboard_niu())
        self.append(2)  # What's this?
        self.append(0)  # Conquest stuff?
        self.append(30)  # Conquest ?
