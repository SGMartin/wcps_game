import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User


from wcps_game.game.constants import RoomStatus
from wcps_game.handlers.packet_handler import PacketHandler

"""
DO_VEHICLE_LEAVE_WORLD (0x7511): where a vehicle has come to rest, so the server can place it for
players who join a running match (DO_GDATA_INFO, 0x7510).

The client sends it once after its player gets out, when the vehicle has stopped moving (until then
it keeps sending the UDP vehicle packet); at once when its player is killed inside; and before leaving
the room while still in a vehicle.

  0      vehicle id
  1-3    position of the hull's body (its centre of mass), in the vehicle packets' units: map units / 20
  4-7    rotation of the hull as a quaternion (x, y, z, w)
  8      wheel suspension, "@" plus one character per wheel (see Vehicle.update_string)
  9-16   eight int16: turn and elevation (radians x 360) of up to four turrets

The vehicle's health is not in it: it travels apart.
"""


class LeaveVehicleHandler(PacketHandler):
    async def process(self, user: "User") -> None:

        vehicle_id = int(self.get_block(0))

        coord_X = float(self.get_block(1))
        coord_Y = float(self.get_block(2))
        coord_Z = float(self.get_block(3))

        rotation = [float(self.get_block(block)) for block in range(4, 8)]

        update_string = self.get_block(8)

        # Every client sends the eight turret values; keep the stored ones if a packet comes without them
        has_turrets = len(self.in_packet.blocks) >= 17
        turrets = [int(self.get_block(block)) for block in range(9, 17)] if has_turrets else None

        if user.room is None:
            return

        if user.room.state == RoomStatus.WAITING:
            return

        target_vehicle = user.room.vehicles.get(vehicle_id)

        if target_vehicle is None:
            logging.error(f"Failed to get coords for vehicle {vehicle_id}")
            return

        target_vehicle.update_position({"X": coord_X, "Y": coord_Y, "Z": coord_Z})
        target_vehicle.update_rotation(*rotation)
        target_vehicle.update_string = update_string
        if turrets is not None:
            target_vehicle.turrets = turrets
