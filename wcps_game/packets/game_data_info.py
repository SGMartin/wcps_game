from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.rooms import Room

from wcps_core.constants import ErrorCodes as corerr
from wcps_core.packets import OutPacket
from wcps_game.packets.packet_list import PacketList, ClientXorKeys


class GameDataInfo(OutPacket):
    def __init__(self, room: "Room"):
        super().__init__(
            packet_id=PacketList.DO_GDATA_INFO,
            xor_key=ClientXorKeys.SEND
        )

        self.append(corerr.SUCCESS)
        self.append(len(room.flags))

        for flag in room.flags.values():
            self.append(flag)

        self.append(0)  # index of the game mode 5 key point
        self.append(room.get_player_count())

        players = room.get_all_players()

        for player in players:
            self.append(player.id)
            self.append(-1)  # stored, no client reader found
            self.append(player.kills)
            self.append(player.deaths)
            self.append(player.branch)
            self.append(player.weapon)
            self.append(player.health)
            self.append(player.vehicle_id)
            self.append(player.vehicle_seat)

        vehicles = room.vehicles.values()
        vehicles_to_update = [v for v in vehicles if v.update_string != ""]

        self.append(len(vehicles_to_update))
        if vehicles_to_update:
            for vehicle in vehicles_to_update:
                self.append(vehicle.id)
                self.append(vehicle.health)
                self.append(vehicle.X)
                self.append(vehicle.Y)
                self.append(vehicle.Z)
                self.append(vehicle.rotation_x)
                self.append(vehicle.rotation_y)
                self.append(vehicle.rotation_z)
                self.append(vehicle.rotation_w)
                self.append(vehicle.update_string)
                # Without them, a joiner saw every turret looking straight ahead until its gunner's
                # next UDP packet
                for turret_value in vehicle.turrets:
                    self.append(turret_value)
