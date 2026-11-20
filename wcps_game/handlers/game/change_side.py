from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus, Team


class ChangeSideHandler(GameProcessHandler):
    async def handle(self):

        if self.room.state != RoomStatus.WAITING:
            return

        target_team = int(self.get_block(2))

        if target_team not in [Team.DERBARAN, Team.NIU]:
            return

        if self.player.team == target_team:
            return

        can_switch = await self.room.switch_player_side(player_to_switch=self.player)

        # The client copies the player to slot p1 and makes p2 the master.
        # Answering a failed switch (team full, clan war) with the request's zeros moved the player into
        # slot 0 and the crown to slot 0 on every client: no answer instead.
        if not can_switch:
            return

        self.set_block(2, self.player.team)
        self.set_block(3, self.player.id)  # p1: new slot
        self.set_block(4, self.room.master_slot)  # p2: master slot

        self.answer = True
        await self.room.check_autostart()
