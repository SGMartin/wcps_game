import time

from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.packets.error_codes import RoomKickError
from wcps_game.game.constants import GameMode, RoomStatus


class VoteKickHandler(GameProcessHandler):
    async def handle(self):

        if not self.player.user.authorized:
            return

        is_vote_request = int(self.get_block(2)) == 0
        target_user = int(self.get_block(3))

        # Unused, we can get the handler caller
        #  kicker = int(self.get_block(6))

        if self.room.game_mode == GameMode.FFA or self.room.state == RoomStatus.WAITING:
            return

        if not self.room.enable_votekick:
            self.error_code = RoomKickError.CANNOT_VOTE_KICK_2
            self.answer = True
            return

        # You cannot kick yourself
        # if self.player.id == target_user:
        #     self.error_code = RoomKickError.INVALID_CANDIDATE
        #     self.answer = True
        #     return

        # try to get the target player
        this_player = self.room.players.get(target_user)

        if not this_player:
            self.error_code = RoomKickError.INVALID_CANDIDATE
            self.answer = True
            return

        # You cannot kick a super master in its room
        if this_player.id == self.room.master_slot and self.room.supermaster:
            self.error_code = RoomKickError.INVALID_CANDIDATE
            self.answer = True
            return

        if this_player.team != self.player.team:
            self.error_code = RoomKickError.CANNOT_KICK_OTHER_TEAM
            self.answer = True
            return

        if self.room.votekick.running and is_vote_request:
            self.error_code = RoomKickError.VOTE_KICK_IN_PROGRESS
            self.answer = True
            return

        if self.room.votekick.last_kick_timestamp + 60 >= time.time():
            self.error_code = RoomKickError.CANNOT_VOTE_KICK
            self.answer = True
            return

        # Tell the game the vote kick started
        if not self.room.votekick.running and is_vote_request:
            self.room.votekick.start_vote(target_slot=this_player.id, side=this_player.team)
            self.set_block(2, 1)
            self.set_block(6, self.player.id)  # kicker id
            self.answer = True
        # It seems chapter 1 only sends the packet back if the user says "YES"
        else:
            # TODO: some msg should be added here
            self.room.votekick.add_user_vote(user=self.player.user, kick=True)