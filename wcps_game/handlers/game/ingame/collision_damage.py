from wcps_game.game.constants import RoomStatus
from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.game_process import GameProcess
from wcps_game.packets.manual_vehicle_explosion import ManualVehicleExplosion


class CollisionDamageHandler(GameProcessHandler):
    async def handle(self):

        if not self.player.user.authorized:
            return

        if self.room.state == RoomStatus.WAITING:
            return

        is_player = bool(int(self.get_block(2)))
        target_vehicle = int(self.get_block(4))
        damage_sustained = int(self.get_block(5))
        out_of_playable_zone = int(self.get_block(6))  # TODO what are you doing soldier!

        if damage_sustained <= 0:
            return

        if not is_player:
            # TODO: vehicles
            target_vehicle = self.room.vehicles.get(target_vehicle)
            if not target_vehicle:
                return

            if out_of_playable_zone != 1:
                target_vehicle.health -= damage_sustained
            else:
                target_vehicle.health = 0
                damage_sustained = target_vehicle.health

            if target_vehicle.health <= 0:
                target_vehicle.health = 0

                # Now wipe every player seat
                for seat in target_vehicle.seats.values():
                    if seat.player is None:
                        continue

                    if seat.player.health <= 0:
                        continue

                    await seat.player.add_deaths()
                    await self.room.current_game_mode.on_suicide(seat.player)

                    # Ugly, but it's best to build here a player suicide packet
                    packet_buffer = []
                    packet_buffer.append(1)
                    packet_buffer.append(seat.player.id)
                    packet_buffer.append(self.room.id)
                    packet_buffer.append(self.packet.blocks[2])
                    packet_buffer.append(PacketList.DO_SUICIDE)
                    packet_buffer.extend(self.blocks)
                    packet_buffer[23] = "$"

                    await self.room.send(GameProcess(packet_buffer).build())

                # Finally, destroy the vehicle
                vehicle_explosion = ManualVehicleExplosion(
                    room=self.room,
                    target_vehicle=target_vehicle
                    )
                await self.room.send(vehicle_explosion.build())
            else:
                self.set_block(7, damage_sustained)
                self.set_block(8, target_vehicle.health)
                self.answer = True
        else:
            if not self.player.alive:
                return

            self.player.health -= damage_sustained

            # The player is killed because of the fall. Oddly, the game sends a suicide subpacket
            if self.player.health < 0:
                self.player.health = 0
                await self.player.add_deaths()
                await self.room.current_game_mode.on_suicide(player=self.player)

                self.set_block(2, self.player.id)
                self.sub_packet = PacketList.DO_SUICIDE

            self.set_block(7, damage_sustained)
            self.set_block(8, self.player.health)
            self.answer = True
