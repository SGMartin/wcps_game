from wcps_game.game.constants import RoomStatus, DeathCause
from wcps_game.handlers.packet_handler import GameProcessHandler
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory


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
                    # Kept apart: the death frees the seat (seat.player becomes None)
                    occupant = seat.player
                    if occupant is None:
                        continue

                    if occupant.health <= 0:
                        continue

                    await occupant.add_deaths()
                    await self.room.current_game_mode.on_suicide(occupant)

                    # The crash packet's p1 (0xc) is no death cause the client knows: no message
                    occupant_death = PacketFactory.create_packet(
                        packet_id=PacketList.DO_SUICIDE,
                        room=self.room,
                        player=occupant,
                        suicide_type=DeathCause.VEHICLE,
                        out_of_map_limits=False,
                    )
                    await self.room.send(occupant_death.build())

                # Finally, destroy the vehicle
                vehicle_explosion = PacketFactory.create_packet(
                    packet_id=PacketList.DO_UNIT_DIE,
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
            if self.player.health <= 0:  # exactly 0 HP is dead too
                self.player.health = 0
                await self.player.add_deaths()
                await self.room.current_game_mode.on_suicide(player=self.player)

                self.set_block(2, self.player.id)
                self.sub_packet = PacketList.DO_SUICIDE

            self.set_block(7, damage_sustained)
            self.set_block(8, self.player.health)
            self.answer = True
