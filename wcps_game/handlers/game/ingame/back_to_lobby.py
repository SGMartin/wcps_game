from wcps_game.game.constants import RoomStatus
from wcps_game.handlers.packet_handler import GameProcessHandler


class BackToLobbyHandler(GameProcessHandler):
    async def handle(self):
        if self.room.state == RoomStatus.WAITING:

            if self.player.state != RoomStatus.WAITING:
                self.player.state = RoomStatus.WAITING

                self.answer = True
                self.self_target = True

                # The lobby shows the room as Playing until every player is back (Room.lobby_state):
                # the last one to come back turns it to Waiting
                await self.room.notify_lobby()

                if self.player.user.room is None:
                    self.player.user.set_room(None, 0)

                    await self.room.channel.send_user_list(self.player.user)
