import asyncio
import time

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room

from wcps_game.game.base_game_mode import BaseGameMode
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory

import wcps_game.game.constants as gconstants


class Explosive(BaseGameMode):
    def __init__(self):
        super().__init__(id=gconstants.GameMode.EXPLOSIVE, name="Explosive")

        self._spawn_lock = asyncio.Lock()

        # game related data
        self.round_end_time = 0
        self.rounds_passed = 0
        self.rounds_limit = 0
        self.bomb_planted = False
        self.bomb_defused = False
        self.bomb_side = -1

        self.active_round = False

        self.team_rounds = {gconstants.Team.DERBARAN: 0, gconstants.Team.NIU: 0}

        self.alive_players = {gconstants.Team.DERBARAN: 0, gconstants.Team.NIU: 0}

    def initialize(self, room: "Room"):
        super().initialize(room)

        self.rounds_limit = room.rounds
        self.initialized = True
        self.prepare_round(is_first_round=True)
        self.active_round = True

    def winner(self):
        derb_rounds = self.team_rounds[gconstants.Team.DERBARAN]
        niu_rounds = self.team_rounds[gconstants.Team.NIU]

        # No ties possible
        if derb_rounds > niu_rounds:
            return gconstants.Team.DERBARAN
        else:
            return gconstants.Team.NONE

    def is_goal_reached(self):
        derb_rounds = self.team_rounds[gconstants.Team.DERBARAN]
        niu_rounds = self.team_rounds[gconstants.Team.NIU]

        if derb_rounds == self.rounds_limit or niu_rounds == self.rounds_limit:
            return True
        else:
            return False

    def current_round_derbaran(self):
        return self.team_rounds[gconstants.Team.DERBARAN]

    def current_round_niu(self):
        return self.team_rounds[gconstants.Team.NIU]

    # Unused in explosives
    def scoreboard_derbaran(self):
        return 0

    # Unused in explosives
    def scoreboard_niu(self):
        return 0

    # TODO: Anything worth doing here?
    # Maybe some stats or background task?
    async def on_death(self):
        pass

    async def on_suicide(self):
        pass

    async def on_flag_capture(self, player, flag_status):
        raise NotImplementedError

    async def process(self):
        if not self.active_round and self.prepare_round(is_first_round=False):
            self.active_round = True

        if self.active_round:
            players = self.room.get_all_players()

            # Update alive players here
            # TODO: extract to func
            for player in players:
                if player.health > 0 and player.alive:
                    if player.team == gconstants.Team.DERBARAN:
                        self.alive_players[gconstants.Team.DERBARAN] += 1
                    else:
                        self.alive_players[gconstants.Team.NIU] += 1

            if not self.is_round_running():
                winner = self.winning_round_team()

                if self.team_rounds[winner] < self.rounds_limit:
                    self.end_round(winner_team=winner)
                else:
                    self.room.end_game(winner_team=self.winner())

    def prepare_round(self, is_first_round: bool = False) -> bool:

        milliseconds_elapsed = time.time() - self.round_end_time
        milliseconds_elapsed = milliseconds_elapsed * 1000

        # Let 5 seconds pass for the end round sequence
        # TODO: make this configurable?
        if milliseconds_elapsed >= 5000:
            self.freeze_tick = False

        # Clear ground items dictionary at the start of each round
        self.room.ground_items.clear()

        players = self.room.get_all_players()
        all_players_ready = True

        for player in players:

            # If any player is still waiting, set the
            # flag to false
            if player.round_waiting:
                all_players_ready = False

            if player.health > 0 and player.alive:
                if player.team == gconstants.Team.DERBARAN:
                    self.alive_players[gconstants.Team.DERBARAN] += 1
                else:
                    self.alive_players[gconstants.Team.NIU] += 1

        if not is_first_round:
            self.rounds_passed += 1

            if not all_players_ready:
                return False

            # If any team is empty, end the game now
            # TODO: move to is_goal_reached?
            if (
                self.alive_players[gconstants.Team.DERBARAN] == 0
                or self.alive_players[gconstants.Team.NIU]
            ):
                winner = gconstants.Team.NONE
                if self.alive_players[gconstants.Team.DERBARAN] > 0:
                    winner = gconstants.Team.DERBARAN
                elif self.alive_players[gconstants.Team.NIU] > 0:
                    winner = gconstants.Team.NIU

                self.room.end_game(winner_team=winner)
                return False

            # Should these be sent from here?
            mission_packet = PacketFactory.create_packet(
                packet_id=PacketList.DO_GO, room=self.room
            )
            round_start_packet = PacketFactory.create_packet(
                packet_id=PacketList.DO_ROUND_START, room=self.room
            )
            await self.room.send(mission_packet.build())
            await self.room.send(round_start_packet.build())
            return True

        return False

    def end_round(self, winner_team: gconstants.Team.NONE):
        self.active_round = False
        self.round_end_time = time.time()
        self.freeze_tick = True

        players = self.room.get_all_players()

        for player in players:
            player.end_round()

        if winner_team != gconstants.Team.NONE:
            self.team_rounds[winner_team] += 1

            round_end_packet = PacketFactory.create_packet(
                packet_id=PacketList.DO_ROUND_END,
                room=self.room,
                winning_team=winner_team,
            )
            await self.room.send(round_end_packet.build())

    def winning_round_team(self):
        # NIU wins on bomb defuse
        if self.bomb_planted and self.bomb_defused:
            return gconstants.Team.NIU
        # NIU wins if the bomb is not planted and derbarans are eliminated
        elif (
            not self.bomb_planted and self.alive_players[gconstants.Team.DERBARAN] == 0
        ):
            return gconstants.Team.NIU
        # NIU also wins if the bomb was not planted and the round timer reaches 0
        elif not self.bomb_planted and self.room.down_ticks <= 0:
            return gconstants.Team.NIU
        # Else, derbaran is winning
        else:
            return gconstants.Team.DERBARAN

    def is_round_running(self):
        # Deb : DEAD + NO BOMB
        if self.alive_players[gconstants.Team.Derbaran] == 0 and not self.bomb_planted:
            return False

        # NIU : DEAD
        if self.alive_players[gconstants.Team.NIU] == 0:
            return False

        # Bomb = Defused
        if self.bomb_planted and self.bomb_defused:
            return False

        # Time is up
        if self.room.down_ticks <= 0:
            return False

        return True

    def handle_explosives():
        pass