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

        if can_switch:
            self.set_block(2, self.player.team)
            self.set_block(3, self.player.id)
            self.set_block(4, self.room.master_slot)

        self.answer = True
