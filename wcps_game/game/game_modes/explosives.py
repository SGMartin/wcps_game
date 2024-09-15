import asyncio
import time

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room

from wcps_game.config import settings
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

    async def initialize(self, room: "Room"):
        await super().initialize(room)

        self.rounds_limit = room.rounds
        self.initialized = True
        await self.prepare_round(is_first_round=True)
        self.active_round = True

    def winner(self):
        rounds = {
            gconstants.Team.DERBARAN: self.team_rounds.get(gconstants.Team.DERBARAN, 0),
            gconstants.Team.NIU: self.team_rounds.get(gconstants.Team.NIU, 0),
        }
        winning_team = max(rounds, key=rounds.get)
        return (
            winning_team
            if rounds[gconstants.Team.DERBARAN] != rounds[gconstants.Team.NIU]
            else gconstants.Team.NONE
        )

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

    # Used to show alive players in each team
    def scoreboard_derbaran(self):
        return self.alive_players[gconstants.Team.DERBARAN]

    def scoreboard_niu(self):
        return self.alive_players[gconstants.Team.NIU]

    # TODO: Anything worth doing here?
    # Maybe some stats or background task?
    async def on_death(self, killer, victim):
        pass

    async def on_suicide(self, player):
        pass

    async def on_flag_capture(self, player, flag_status):
        raise NotImplementedError

    async def handle_explosives(self, player) -> bool:

        if player.team == gconstants.Team.DERBARAN:
            # TODO: statistics here
            player.bombs_planted += 1
            self.bomb_planted = True

            self.room.down_ticks = settings().explosive_bomb_time * 1000
            return True
        else:
            if self.bomb_planted:
                player.bombs_defused += 1
                self.bomb_defused = True
                return True
            else:
                return False

    async def process(self):
        if not self.active_round and await self.prepare_round(is_first_round=False):
            self.active_round = True

        if self.active_round:
            players = self.room.get_all_players()

            # Update alive players here
            # TODO: extract to func
            derbaran_alive = 0
            niu_alive = 0
            for player in players:
                if player.health > 0 and player.alive:
                    if player.team == gconstants.Team.DERBARAN:
                        derbaran_alive += 1
                    else:
                        niu_alive += 1

            # Update alive players count
            self.alive_players[gconstants.Team.DERBARAN] = derbaran_alive
            self.alive_players[gconstants.Team.NIU] = niu_alive

            if not self.is_round_running():
                winner = self.winning_round_team()

                if (
                    self.room.get_player_count() <= 1
                    or self.team_rounds[winner] >= self.rounds_limit
                ):
                    await self.room.end_game(winner_team=self.winner())
                else:
                    await self.end_round(winner_team=winner)

    async def prepare_round(self, is_first_round: bool = False) -> bool:

        milliseconds_elapsed = time.time() - self.round_end_time
        milliseconds_elapsed = milliseconds_elapsed * 1000

        if not milliseconds_elapsed >= 5000:
            return False

        # let the clock tick again after the 5 seconds of elapsed time have passed
        self.freeze_tick = False

        # Clear ground items dictionary at the start of each round
        self.room.ground_items.clear()
        self.room.up_ticks = 0

        self.room.down_ticks = settings().explosive_round_time * 1000
        self.bomb_planted = False
        self.bomb_defused = False

        # Nothing left to do here
        if is_first_round:
            return False

        players = self.room.get_all_players()
        all_players_ready = True

        alive_derbaran = 0
        alive_niu = 0

        for player in players:

            # If any player is still waiting, set the
            # flag to false
            if player.round_waiting:
                all_players_ready = False

            if player.health > 0 and player.alive:
                if player.team == gconstants.Team.DERBARAN:
                    alive_derbaran += 1
                else:
                    alive_niu += 1

        # Update alive players counter
        self.alive_players[gconstants.Team.DERBARAN] = alive_derbaran
        self.alive_players[gconstants.Team.NIU] = alive_niu

        self.rounds_passed += 1

        if not all_players_ready:
            return False

        if (
            self.alive_players[gconstants.Team.DERBARAN] == 0
            or self.alive_players[gconstants.Team.NIU] == 0
        ):
            winner = gconstants.Team.NONE
            if self.alive_players[gconstants.Team.DERBARAN] > 0:
                winner = gconstants.Team.DERBARAN
            elif self.alive_players[gconstants.Team.NIU] > 0:
                winner = gconstants.Team.NIU

            await self.room.end_game(winner_team=winner)
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

    async def end_round(self, winner_team: gconstants.Team.NONE):
        self.active_round = False
        self.round_end_time = time.time()
        self.freeze_tick = True

        players = self.room.get_all_players()

        for player in players:
            await player.end_round()

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
        if self.alive_players[gconstants.Team.DERBARAN] == 0 and not self.bomb_planted:
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
