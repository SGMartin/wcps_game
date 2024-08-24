from wcps_core.packets import OutPacket
from wcps_game.packets.packet_list import ClientXorKeys, PacketList

# Done by me to avoid creating a game data packet from scratch when I have to kill
# seated players in a vehicle for instance


class ManualVehicleExplosion(OutPacket):
    def __init__(self, room, target_vehicle):
        super().__init__(
            packet_id=PacketList.DO_GAME_PROCESS,
            xor_key=ClientXorKeys.SEND
        )

        self.append(1)
        self.append(-1)
        self.append(room.id)
        self.append(2)
        self.append(PacketList.DO_UNIT_DIE)
        self.append(0)
        self.append(1)
        self.append(0)
        self.append(target_vehicle.id)
        self.append(0)
        self.append(2)
        self.append(0)
        self.append(7)
        self.append(2)
        self.append(0)
        self.append(1)
        self.append(100)
        self.append(0)
        self.append(0)
        self.append(target_vehicle.X)
        self.append(target_vehicle.Y)
        self.append(target_vehicle.Z)
        self.append(0)
        self.append(0)
        self.append(0)
        self.append(0)
        self.append(0)
        self.append("FFFF")
