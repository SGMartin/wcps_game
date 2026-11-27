from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room

from wcps_core.constants import ErrorCodes
from wcps_core.packets import OutPacket

from wcps_game.game.constants import GameMode, Team
from wcps_game.packets.packet_list import PacketList, ClientXorKeys


class EndGame(OutPacket):
    def __init__(self, room: "Room", players: list, winner_team: Team):
        super().__init__(
            packet_id=PacketList.DO_GAME_RESULT,
            xor_key=ClientXorKeys.SEND
        )

        self.append(ErrorCodes.SUCCESS)
        # The client's "win/lose" per team. It takes the winner from these two alone: Derbaran if its value
        # is greater, NIU otherwise, and shows each player "your team won" or "lost" against their own
        # team. Explosive sends the rounds each team won. The ticket modes have no rounds and used to send
        # 0 / 0, which made NIU the winner of every match: Derbaran saw "your team lost" after winning.
        # They now send 1 for the winner and 0 for the loser. The client has no tie: 0 / 0 shows NIU won.
        if room.game_mode in (GameMode.TDM, GameMode.CONQUEST):
            self.append(int(winner_team == Team.DERBARAN))
            self.append(int(winner_team == Team.NIU))
        else:
            self.append(room.current_game_mode.current_round_derbaran())
            self.append(room.current_game_mode.current_round_niu())

        derbaran_kills = 0
        niu_kills = 0
        derbaran_deaths = 0
        niu_deaths = 0

        for player in players:
            if player.team == Team.DERBARAN:
                derbaran_kills += player.kills
                derbaran_deaths += player.deaths
            else:
                niu_kills += player.kills
                niu_deaths += player.deaths

        # Team totals in the order the client reads them: kills D/N, deaths D/N, team score D/N
        self.append(derbaran_kills)
        self.append(niu_kills)
        self.append(derbaran_deaths)
        self.append(niu_deaths)
        self.append(room.current_game_mode.scoreboard_derbaran())
        self.append(room.current_game_mode.scoreboard_niu())
        self.append(len(players))

        for player in players:
            self.append(player.id)
            self.append(player.kills)
            self.append(player.deaths)
            self.append(player.flags_taken)
            self.append(player.points)
            self.append(player.money_earned)
            self.append(player.xp_earned)
            self.append(player.user.xp)

        self.append(room.master_slot)
