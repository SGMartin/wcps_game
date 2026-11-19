from wcps_core.packets import OutPacket

from wcps_game.packets.packet_list import PacketList, ClientXorKeys


class GameLaunchClock(OutPacket):
    """Auto Start countdown, one per second. The client (PF23 0x5f7450) shows, from the seconds left:
    20 -> m29 "Game starts in 20 seconds" and m30 "May change game settings within 10 seconds",
    every 5 -> m31 "Exit if you do not want to play", always -> m32 "Starting the game N !" (red from 10).
    In clan war rooms it counts minutes instead (m775-m777)."""

    def __init__(self, seconds: int):
        super().__init__(
            packet_id=PacketList.DO_GAME_LAUNCH_CLOCK,
            xor_key=ClientXorKeys.SEND
        )
        self.append(seconds)
