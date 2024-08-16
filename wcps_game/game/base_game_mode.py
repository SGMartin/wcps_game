from abc import ABC, abstractmethod

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.handlers.packet_handler import GameProcessHandler
    from wcps_game.game.player import Player

from wcps_game.game.constants import GameMode, HitboxBone, DamageTypes, DamageMultipliers, DamageDistances, DefaultWeapon
from wcps_game.client.items import ItemDatabase
from wcps_game.packets.packet_list import PacketList


class BaseGameMode(ABC):
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
        self.room = None
        self.initialized = False
        self.freeze_tick = False

    def initialize(self, room):
        self.room = room

    @abstractmethod
    def is_goal_reached(self) -> bool:
        pass

    @abstractmethod
    def winner(self):
        pass

    @abstractmethod
    def process(self):
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
    def on_death(self, killer, target):
        pass

    def get_spawn_id(self) -> int:
        return 0

    async def on_damage(self, damage_handler: "GameProcessHandler"):
        # 30000 0 0 2 103 0 1 1 4 0 14 0 14 2 0 0 1242 0 0 3682.5825 183.8098 2690.4419 4.0000 0 0 3.0000 0 DC04 \n')
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

        if not is_player:
            print("OBJECT DAMAGE NOT IMPLEMENTED YET")
            return

        # Validate the weapon
        item_database = ItemDatabase()

        if not item_database.is_active(weapon_code):
            # TODO: log this? cheater?
            print(f"Weapon {weapon_code} is not yet implemented")
            return

        if not attacker.user.inventory.has_item(weapon_code) and weapon_code not in DefaultWeapon.DEFAULTS:
            # TODO: cheater?
            print(f"Weapon {weapon_code} is not in {attacker.user.displayname} inventory")
            return

        if not self.can_be_damaged(attacker=attacker, victim=victim):
            print(f"{attacker.user.displayname} cannot damage {victim.user.displayname}")
            return

        if not item_database.is_weapon(weapon_code):
            print(f"{weapon_code} is not a weapon")
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
            radius=radius
        )
        await self.damage_player(
            handler=damage_handler,
            attacker=attacker,
            victim=victim,
            damage=damage_taken,
            is_headshot=is_headshot
        )

    async def damage_player(self, handler: "GameProcessHandler", attacker: "Player", victim: "Player", damage: int, is_headshot: bool = False):

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

        handler.set_block(12, victim.health)
        handler.set_block(13, current_victim_health)
        handler.answer = True

    def can_be_damaged(self, attacker: "Player", victim: "Player"):
        can_be_damaged = False

        if victim.spawn_protection_ticks > 0:
            return can_be_damaged

        if not attacker.alive or attacker.health <= 0:
            return can_be_damaged

        if not victim.alive or victim.health <= 0:
            return can_be_damaged

        if attacker.team == victim.team and self.room.game_mode != GameMode.FFA:
            return can_be_damaged

        can_be_damaged = True
        return can_be_damaged

    def damage_calculator(self, weapon: str, damage_type: int, hitbox: int, distance: int, radius: int):
        item_database = ItemDatabase()

        damage_taken = 0

        # This is the raw power of the weapon
        weapon_power = item_database.get_weapon_power(code=weapon)
        # A list of coefs. for personal/surface/air/ship etc.
        damage_type_coefs = item_database.get_weapon_damage_class(
            code=weapon,
            damage_class=damage_type
            )
        # Distance can only be short / mid / long
        damage_type = damage_type_coefs[DamageDistances.SHORT] / 100  # TODO: DISTANCE HERE

        # Hitbox
        bone_multipliers = {
            HitboxBone.HEADNECK: DamageMultipliers.HEADNECK,
            HitboxBone.TORSOLIMBS: DamageMultipliers.TORSOLIMBS,
            HitboxBone.FEETHANDS: DamageMultipliers.FEETHANDS
        }

        bone_coef = bone_multipliers[hitbox] / 100

        if radius > 0:  # Then it is a radius damage
            radius_coef = radius / 100
            damage_taken = weapon_power * radius_coef * damage_type
        else:
            damage_taken = weapon_power * damage_type * bone_coef

        final_damage = round(damage_taken)
        print(f"Final damage for this player: {weapon}: {weapon_power} * {radius_coef} * {damage_type} * {bone_coef}")
        return final_damage
