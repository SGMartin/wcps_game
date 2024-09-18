from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room

from wcps_core.packets import OutPacket
from wcps_game.packets.packet_list import PacketList, ClientXorKeys


class UpdateGameData(OutPacket):
    def __init__(self, room: "Room"):
        super().__init__(
            packet_id=PacketList.DO_GAME_UPDATE_DATA,
            xor_key=ClientXorKeys.SEND
        )

        self.append(room.get_player_count())

        room_players = room.get_all_players()

        for player in room_players:
            self.append(player.id)
            self.append(player.health)
            self.append(player.vehicle_id)
            self.append(player.vehicle_seat)

        self.append(len(room.vehicles))
        # Reverse engineered by trial and error in the pserver
        # Most sources expand this part of the packet with more info
        # But PF20 just requires the veh health?
        for vehicle in room.vehicles.values():
            self.append(vehicle.health)
