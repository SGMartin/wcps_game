from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User


from wcps_game.game.constants import RoomStatus
from wcps_game.handlers.packet_handler import PacketHandler

"""
This handler handles packet 29969. Not all sources have it. It is sent right after you
answer to the usual LeaveVehicle subpacket for packet 30000. It seems to report the vehicle
coordinates so that the room can keep them stored for a full game update packet later.
"""


class LeaveVehicleHandler(PacketHandler):
    async def process(self, user: "User") -> None:

        vehicle_id = int(self.get_block(0))

        coord_X = float(self.get_block(1))
        coord_Y = float(self.get_block(2))
        coord_Z = float(self.get_block(3))

        angle_X = float(self.get_block(4))
        angle_Y = float(self.get_block(5))
        angle_Z = float(self.get_block(6))

        # Unsure
        turret_angle = float(self.get_block(7))

        update_string = self.get_block(8)

        if user.room is None:
            return

        if user.room.state == RoomStatus.WAITING:
            return

        target_vehicle = user.room.vehicles.get(vehicle_id)

        if target_vehicle is None:
            print(f"Failed to get coords for vehicle {target_vehicle}")

        target_vehicle.update_position({"X": coord_X, "Y": coord_Y, "Z": coord_Z})
        target_vehicle.update_angles({"X": angle_X, "Y": angle_Y, "Z": angle_Z})
        target_vehicle.turret_angle = turret_angle
        target_vehicle.update_string = update_string
