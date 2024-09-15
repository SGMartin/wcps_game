import asyncio
import logging

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.handlers.packet_handler import GameProcessHandler
    from wcps_game.game.player import Player

from wcps_game.game.constants import (
    Classes,
    GameMode,
    HitboxBone,
    DamageTypes,
    DamageMultipliers,
    DamageDistances,
    DefaultWeapon,
    Team,
)
from wcps_game.client.items import ItemDatabase
from wcps_game.packets.packet_list import PacketList


class BaseGameMode(ABC):
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
        self.room = None
        self.initialized = False
        self.freeze_tick = False

    async def initialize(self, room):
        self.room = room

    @abstractmethod
    def is_goal_reached(self) -> bool:
        pass

    @abstractmethod
    def winner(self):
        pass

    @abstractmethod
    async def process(self):
        pass

    @abstractmethod
    def current_round_derbaran(self) -> int:
        pass

    @abstractmethod
    def current_round_niu(self) -> int:
        pass

    @abstractmethod
    def scoreboard_derbaran(self) -> int:
        pass

    @abstractmethod
    def scoreboard_niu(self) -> int:
        pass

    @abstractmethod
    async def on_death(self, killer, victim):
        pass

    @abstractmethod
    async def on_suicide(self, player):
        pass

    @abstractmethod
    async def on_flag_capture(self, player, flag_status):
        pass

    async def handle_explosives(self, player) -> bool:
        return False

    async def get_spawn_id(self) -> int:
        return 0

    async def on_damage(self, damage_handler: "GameProcessHandler"):
        is_player = bool(int(damage_handler.get_block(2)))
        target_id = int(damage_handler.get_block(3))
        is_radius_damage = bool(int(damage_handler.get_block(10)))
        hitbox_location = int(damage_handler.get_block(11))

        weapon_code = damage_handler.get_block(22)

        if is_radius_damage:
            radius = hitbox_location
        else:
            radius = 0
        attacker = damage_handler.player
        victim = damage_handler.room.players[target_id]

        if victim is None:
            return

        # Artillery or vehicle attack
        if not is_player:
            await self.on_object_attack(
                handler=damage_handler, attacker=attacker, victim=victim
            )
            return

        # Validate the weapon
        item_database = ItemDatabase()

        if not item_database.is_active(weapon_code):
            # TODO: log this? cheater?
            logging.error(f"Weapon {weapon_code} is not yet implemented")
            return

        if (
            not attacker.user.inventory.has_item(weapon_code)
            and weapon_code not in DefaultWeapon.DEFAULTS
        ):
            # TODO: cheater?
            logging.error(
                f"Weapon {weapon_code} is not in {attacker.user.displayname} inventory"
            )
            return

        if not self.can_be_damaged(attacker=attacker, victim=victim):
            logging.info(
                f"{attacker.user.displayname} cannot damage {victim.user.displayname}"
            )
            return

        if not item_database.is_weapon(weapon_code):
            logging.info(f"{weapon_code} is not a weapon")
            return

        # WTF WarRock
        bone_id = hitbox_location - attacker.user.session_id
        if "DA" in weapon_code or "DJ" in weapon_code or "DK" in weapon_code:
            can_headhot = False
        else:
            can_headhot = True

        is_headshot = (bone_id == HitboxBone.HEADNECK) and can_headhot

        damage_taken = self.damage_calculator(
            weapon=weapon_code,
            damage_type=DamageTypes.INFANTRY,
            hitbox=bone_id,
            distance=0,  # TODO,
            radius=radius,
        )
        await self.damage_player(
            handler=damage_handler,
            attacker=attacker,
            victim=victim,
            damage=damage_taken,
            is_headshot=is_headshot,
        )

    async def on_object_attack(self, handler: "GameProcessHandler", attacker, victim):
        vehicle_code = handler.get_block(22)

        # We could probably get the vehicle id from the packet, but don't trust the client
        attacker_vehicle = handler.room.vehicles.get(attacker.vehicle_id)

        if attacker_vehicle is None or attacker_vehicle.code != vehicle_code:
            return

        # I could check vehicle health but what about rogue cannon projectiles?
        if not self.can_be_damaged(attacker, victim):
            return

        is_sub_weapon = bool(int(handler.get_block(9)))

        if is_sub_weapon:
            weapon_code = attacker_vehicle.seats[attacker.vehicle_seat].sub_weapon_code
        else:
            weapon_code = attacker_vehicle.seats[attacker.vehicle_seat].main_weapon_code

        # most vehicles use radius calc. even for machine guns but just in case handle everything
        damage_taken = 0

        # is_radius = bool(int(handler.get_block(10)))

        # Vehicles do not use bones, but may set is_radius to FALSE. Use a default bone
        radius = int(handler.get_block(11))
        bone_id = HitboxBone.TORSOLIMBS

        # If radius is 0, it will use the bone_id
        damage_taken = self.damage_calculator(
            weapon=weapon_code,
            damage_type=DamageTypes.INFANTRY,
            hitbox=bone_id,
            distance=0,  # TODO
            radius=radius,
        )
        await self.damage_player(
            handler=handler,
            attacker=attacker,
            victim=victim,
            damage=damage_taken,
            is_headshot=False,  # TODO: Even if we do not display icon we should check this
        )

    async def on_object_damage(self, handler: "GameProcessHandler"):

        # it may be another vehicle
        is_player_attacker = bool(int(handler.get_block(2)))
        # id of the attacked object/vehicle
        object_id = int(handler.get_block(3))

        # slot_id = int(handler.get_block(4)) Unused, we use our own data
        is_sub_weapon = bool(int(handler.get_block(9)))
        # is_radius_weapon = bool(int(handler.get_block(10))) Unused
        radius = int(handler.get_block(11))

        weapon_code = handler.get_block(22)

        attacker = handler.player
        vehicle = handler.room.vehicles.get(object_id)

        if not vehicle:
            return

        if not self.can_be_damaged(attacker=attacker, victim=vehicle):
            return

        # Define the vehicle type of the victim
        damage_taken = 0
        vehicle_class = vehicle.type

        # Player using weapon to attack vehicle
        if is_player_attacker:
            if (
                not attacker.user.inventory.has_item(weapon_code)
                and weapon_code not in DefaultWeapon.DEFAULTS
            ):
                return
            damage_taken = self.damage_calculator(
                weapon=weapon_code,
                damage_type=vehicle_class,
                hitbox=0,  # Vehicles do not have a hitbox AFAIK
                distance=0,  # TODO
                radius=radius,
            )
        else:  # Vehicle - vehicle combat
            if attacker.vehicle_id == -1:  # artillery strike

                if not weapon_code == "FG02":  # Some other environment damage
                    logging.error(f"Unrecognized environment damage {weapon_code}")
                    return
                # Artillery requires binoculars
                if not attacker.user.inventory.has_item("DX01"):
                    return
                # And sniper class
                if not attacker.branch == Classes.SNIPER:
                    return

                damage_taken = self.damage_calculator(
                    weapon="FG02",
                    damage_type=vehicle_class,
                    hitbox=None,
                    distance=0,  # TODO
                    radius=radius,
                )
            else:
                attacker_vehicle = handler.room.vehicles.get(attacker.vehicle_id)

                if not attacker_vehicle.code == weapon_code:
                    logging.error(
                        f"Missmatch in vehicle codes {attacker_vehicle.code}-{weapon_code}"
                    )
                    return

                # we need the actual weapon code of the vehicle in this case
                # Ignore the reported vehicle seat, we stored our own anyway
                if is_sub_weapon:
                    weapon_code = attacker_vehicle.seats[
                        attacker.vehicle_seat
                    ].sub_weapon_code
                else:
                    weapon_code = attacker_vehicle.seats[
                        attacker.vehicle_seat
                    ].main_weapon_code

                damage_taken = self.damage_calculator(
                    weapon=weapon_code,
                    damage_type=vehicle_class,
                    hitbox=None,
                    distance=0,  # TODO
                    radius=radius,
                )

        await self.damage_vehicle(
            handler=handler,
            attacker=attacker,
            vehicle=vehicle,
            damage_taken=damage_taken,
        )

    async def damage_player(
        self,
        handler: "GameProcessHandler",
        attacker: "Player",
        victim: "Player",
        damage: int,
        is_headshot: bool = False,
    ):

        current_victim_health = victim.health
        remaining_victim_health = victim.health - damage

        if remaining_victim_health > 0:
            victim.health = remaining_victim_health
        else:
            victim.health = 0
            handler.sub_packet = PacketList.DO_PLAYER_DIE

            if is_headshot:
                handler.set_block(17, "99.000")  # headshot icon :shrug:

            await victim.add_deaths()
            await attacker.add_kills(headshot=is_headshot)
            await self.on_death(killer=attacker, victim=victim)

        handler.set_block(12, victim.health)
        handler.set_block(13, current_victim_health)
        handler.answer = True

    async def damage_vehicle(
        self, handler: "GameProcessHandler", attacker, vehicle, damage_taken
    ):

        vehicle.health -= damage_taken

        # Vehicle alive
        if vehicle.health > 0:
            handler.sub_packet = PacketList.DO_DAMAGED_UNIT
            handler.set_block(12, vehicle.health)
            handler.set_block(13, damage_taken)

            handler.answer = True
        else:
            vehicle.health = 0
            if (
                vehicle.team != Team.NONE
            ):  # Someone was in the vehicle. We have to kill them
                # avoid circular import
                from wcps_game.handlers.game_handler_factory import (
                    get_subhandler_for_packet,
                )

                for seat in vehicle.seats.values():
                    if seat.player is not None:

                        # Maybe dead from AW50F and failed to update?
                        if seat.player.health <= 0:
                            continue

                        death_handler = get_subhandler_for_packet(
                            subpacket_id=PacketList.DO_PLAYER_DIE
                        )

                        asyncio.create_task(
                            death_handler.process(
                                user=seat.player.user, in_packet=handler.packet
                            )
                        )
                        await attacker.add_kills()
                        await self.on_death(killer=attacker, victim=seat.player)

            # Finally, destroy the vehicle
            handler.sub_packet = PacketList.DO_UNIT_DIE
            handler.set_block(12, vehicle.health)
            handler.set_block(13, damage_taken)
            handler.answer = True

    def can_be_damaged(self, attacker: "Player", victim: "Player"):
        can_be_damaged = False

        # Make sure no damage can be taken in explosive after the bomb is defused or explodes
        this_room = attacker.user.room

        if (
            this_room.game_mode == GameMode.EXPLOSIVE
            and not this_room.current_game_mode.active_round
        ):
            return can_be_damaged

        if victim.spawn_protection_ticks > 0:
            return can_be_damaged

        if attacker.health <= 0:
            return can_be_damaged

        if victim.health <= 0:
            return can_be_damaged

        if attacker.team == victim.team and self.room.game_mode != GameMode.FFA:
            return can_be_damaged

        can_be_damaged = True
        return can_be_damaged

    def damage_calculator(
        self, weapon: str, damage_type: int, hitbox: int, distance: int, radius: int
    ):
        item_database = ItemDatabase()
        is_vehicle_weapon = weapon[0] == "F"  # items settings in items-bin defines this

        damage_taken = 0

        # This is the raw power of the weapon
        weapon_power = item_database.get_weapon_power(
            code=weapon, is_vehicle=is_vehicle_weapon
        )
        # A list of coefs. for personal/surface/air/ship etc.
        damage_type_coefs = item_database.get_weapon_damage_class(
            code=weapon, damage_class=damage_type, is_vehicle=is_vehicle_weapon
        )
        # Distance can only be short / mid / long
        damage_type = (
            damage_type_coefs[DamageDistances.SHORT] / 100
        )  # TODO: DISTANCE HERE

        if radius > 0 or not hitbox:  # Then it is a radius damage
            radius_coef = radius / 100
            damage_taken = weapon_power * radius_coef * damage_type
        else:
            # Hitbox
            bone_multipliers = {
                HitboxBone.HEADNECK: DamageMultipliers.HEADNECK,
                HitboxBone.TORSOLIMBS: DamageMultipliers.TORSOLIMBS,
                HitboxBone.FEETHANDS: DamageMultipliers.FEETHANDS,
            }
            bone_coef = bone_multipliers[hitbox] / 100
            damage_taken = weapon_power * damage_type * bone_coef

        final_damage = round(damage_taken)
        return final_damage
