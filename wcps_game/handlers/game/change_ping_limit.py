from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.game.constants import RoomStatus, RoomPingLimit


class ChangePingLimitHandler(GameProcessHandler):
    async def handle(self):
        if self.player.id != self.room.master_slot:  # This player is not the master
            # TODO: log this? Cheater?
            return

        if self.room.state != RoomStatus.WAITING:
            return

        target_ping = int(self.get_block(2))

        if target_ping > RoomPingLimit.ALL:
            target_ping = RoomPingLimit.GREEN

        self.room.ping_limit = target_ping

        self.set_block(2, self.room.ping_limit)
        self.update_lobby = True
        self.answer = True
