import logging

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room

from wcps_core.constants import ErrorCodes
from wcps_core.packets import OutPacket

from wcps_game.game.constants import Team
from wcps_game.packets.packet_list import PacketList, ClientXorKeys


class EndGame(OutPacket):
    def __init__(self, room: "Room", players: list, winner_team: Team):
        super().__init__(
            packet_id=PacketList.DO_GAME_RESULT,
            xor_key=ClientXorKeys.SEND
        )

        self.append(ErrorCodes.SUCCESS)

        if room.current_game_mode is not None:
            self.append(room.current_game_mode.current_round_derbaran())
            self.append(room.current_game_mode.current_round_niu())
        else:
            # FFA CRASH. TODO: INVESTIGATE IF IT HAPPENS
            self.fill(0, 2)
            logging.info(f"WARNING: FFA CRASH FOR ROOM {room.id}")

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

        self.append(derbaran_kills)
        self.append(derbaran_deaths)
        self.append(niu_kills)
        self.append(niu_deaths)
        self.append(0)
        self.append(0)
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
