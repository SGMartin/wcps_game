from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus


class CaptureFlagHandler(GameProcessHandler):
    """DO_CONQUEST_CAMP 0x9c. The client sets flag p0 to owner p1 and picks the message
    relative to the local side: p1 < 0 neutralised (m58); p1 = own side and p2 = own side "recaptured"
    (m59); p1 = own side and p2 != own side "secured" (m60); p1 = enemy "captured by the enemy" (m61).
    p2 is the team that owned the flag before it went neutral (or its starting owner)."""

    async def handle(self):

        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.WAITING:
            return

        if not self.player.alive:
            return

        if self.player.team is None:
            return

        captured_flag_id = int(self.get_block(2))

        if captured_flag_id not in self.room.flags:
            return

        # Fine even for conquest since we flush spawn_flags
        if captured_flag_id in self.room.spawn_flags.values():
            return

        old_flag_team = self.room.flags[captured_flag_id]

        # Two teammates finishing the same capture: the second one would neutralise their own flag
        if old_flag_team == self.player.team:
            return

        if old_flag_team == -1:
            # Neutral flag taken: "recaptured" if it was ours before going neutral
            previous_owner = self.room.flag_last_owner.get(captured_flag_id, -1)
            self.room.flags[captured_flag_id] = self.player.team
            self.room.flag_last_owner[captured_flag_id] = self.player.team
        else:
            # Enemy flag neutralised: remember whose it was
            previous_owner = old_flag_team
            self.room.flags[captured_flag_id] = -1
            self.room.flag_last_owner[captured_flag_id] = old_flag_team

        self.set_block(2, captured_flag_id)  # p0
        self.set_block(3, self.room.flags[captured_flag_id])  # p1: new owner (-1 neutral)
        self.set_block(4, previous_owner)  # p2
        self.answer = True

        await self.player.add_flags()
        await self.room.current_game_mode.on_flag_capture(
            player=self.player,
            flag_status=old_flag_team
            )
