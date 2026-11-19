from wcps_game.game.constants import RoomStatus, DeathCause

# Fixed environment damage per tick: under water, flipped, boat beached, danger zone
VEHICLE_ENVIRONMENT_DAMAGE = (60, 20, 10, 100)
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
        damage_sustained = int(self.get_block(5))  # p3
        # p4 (client senders 0x47ddb0 / 0x47dc60): 1 = fixed environment damage in p3, sent every tick
        # (under water 60, flipped 20, boat beached 10, danger zone 100); > 1 = divisor of a speed crash
        damage_kind = int(self.get_block(6))

        if damage_sustained <= 0:
            return

        if not is_player:
            target_vehicle = self.room.vehicles.get(target_vehicle)
            if not target_vehicle:
                return

            if damage_kind == 1:
                # It used to blow the vehicle up at once (read as "out of playable zone"). The server only
                # takes the damage values the client can send
                if damage_sustained not in VEHICLE_ENVIRONMENT_DAMAGE:
                    return
            # TODO speed crash (damage_kind > 1): p3 is the speed and p4 the divisor; check in game whether
            # the damage should be p3 // p4 before changing it (#66)
            target_vehicle.health -= damage_sustained

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

                    # The crash packet's p1 (0xc) is no death cause the client knows: no message
                    occupant_death = PacketFactory.create_packet(
                        packet_id=PacketList.DO_SUICIDE,
                        room=self.room,
                        player=seat.player,
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
