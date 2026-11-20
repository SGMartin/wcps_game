from wcps_core.packets import OutPacket
from wcps_game.packets.packet_list import ClientXorKeys, PacketList

# Done by me to avoid creating a game data packet from scratch when I have to spawn vehicles


class VehicleSpawn(OutPacket):
    def __init__(self, room, target_vehicle):
        super().__init__(
            packet_id=PacketList.DO_GAME_PROCESS,
            xor_key=ClientXorKeys.SEND
        )

        # The client's UNIT_REGEN handler only reads p0; everything after it is ignored
        self.append(1)
        self.append(-1)
        self.append(room.id)
        self.append(2)
        self.append(PacketList.DO_UNIT_REGEN)
        self.append(0)
        self.append(1)
        # p0: index in the map's vehicle list. The client respawns that vehicle, reloads its max
        # health from the vehicle data and prints "<code> has re-spawned" (m54)
        self.append(target_vehicle.id)
        self.append(500)
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
        self.append(target_vehicle.spawn_X)  # coords and rotations: not read by the client
        self.append(target_vehicle.spawn_Y)
        self.append(target_vehicle.spawn_Z)
        self.append(target_vehicle.angular_X)
        self.append(target_vehicle.angular_Y)
        self.append(target_vehicle.angular_Z)
        self.append(0)
        self.append(0)
        self.append(target_vehicle.code)
