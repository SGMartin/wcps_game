from wcps_core.packets import OutPacket
from wcps_game.packets.packet_list import ClientXorKeys, PacketList

# Done by me to avoid creating a game data packet from scratch when I have to spawn vehicles


class VehicleSpawn(OutPacket):
    def __init__(self, room, target_vehicle):
        super().__init__(
            packet_id=PacketList.DO_GAME_PROCESS,
            xor_key=ClientXorKeys.SEND
        )

        # Most of these bytes are unknown
        # TODO: research them
        self.append(1)
        self.append(-1)
        self.append(room.id)
        self.append(2)
        self.append(PacketList.DO_UNIT_REGEN)
        self.append(0)
        self.append(1)
        self.append(target_vehicle.id)
        self.append(500)  # Unknown
        self.append(0)
        self.append(1)
        self.append(0)
        self.append(15)
        self.append(1)
        self.append(5)
        self.append(1)
        self.append(1090909)
        self.append(-60401)
        self.append(1090909)
        self.append(target_vehicle.spawn_X)  # Assumed as all of the coords
        self.append(target_vehicle.spawn_Y)
        self.append(target_vehicle.spawn_Z)
        self.append(target_vehicle.angular_X)
        self.append(target_vehicle.angular_Y)
        self.append(target_vehicle.angular_Z)
        self.append(0)
        self.append(0)
        self.append(target_vehicle.code)
