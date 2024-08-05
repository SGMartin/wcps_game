from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User


from wcps_game.client.items import ItemDatabase
from wcps_game.handlers.packet_handler import PacketHandler
from wcps_game.game.constants import MAX_WEAPONS_SLOTS, MAX_CLASSES, DefaultWeapon, BranchSlotCodes
from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.error_codes import EquipmentError


class EquipmentHandler(PacketHandler):
    async def process(self, u: "User") -> None:
        # 31184385 29970 0 3 D 2 DC02 2

        # third block is only used if is_item_equip is false
        # it becomes target_slot. Else, use the 5th
        item_database = ItemDatabase()

        is_item_equip = not bool(int(self.get_block(0)))
        target_branch = int(self.get_block(1))
        alt_target_slot = int(self.get_block(3))
        weapon_code = self.get_block(4)
        target_slot = int(self.get_block(5))

        if not u.authorized:
            return

        if target_slot >= MAX_WEAPONS_SLOTS:
            return

        if target_branch >= MAX_CLASSES:
            await u.disconnect()

        if len(weapon_code) != 4:
            return

        if not item_database.item_exists(code=weapon_code):
            return  # Error?

        # let admins use inactive items
        if not item_database.is_active(weapon_code) and u.rights <= 3:
            await u.disconnect()  # potential cheater. Log?

        if (
            not u.inventory.has_item(weapon_code)
            and weapon_code not in DefaultWeapon.DEFAULTS
        ):
            await u.disconnect()  # potential cheater/scripter. Log?

        # is equipped?
        equiped_in_slot = u.inventory.equipment.is_equipped_in_class(
            target_class=target_branch, weapon=weapon_code
        )

        if not is_item_equip:  # in this case, the user is UNequipping
            if equiped_in_slot >= 0:
                u.inventory.equipment.remove_item_from_slot(
                    target_class=target_branch,
                    target_slot=alt_target_slot
                    )

                unequip_packet = PacketFactory.create_packet(
                    packet_id=PacketList.EQUIPMENT,
                    error_code=1,
                    target_class=target_branch,
                    new_loadout=u.inventory.equipment.loadout[target_branch]
                )
                await u.send(unequip_packet.build())
                return

        if equiped_in_slot >= 0:
            already_equipped_packet = PacketFactory.create_packet(
                packet_id=PacketList.EQUIPMENT,
                error_code=EquipmentError.ALREADY_EQUIPPED
                )
            await u.send(already_equipped_packet.build())
            return
        else:
            # Final check: can you really put a weapon here?
            this_valid_codes = BranchSlotCodes[target_branch][target_slot]
            weapon_subtype = weapon_code[1]

            if weapon_subtype in this_valid_codes:

                # Perform the actual switch
                u.inventory.equipment.add_item_to_slot(
                    target_class=target_branch,
                    target_slot=target_slot,
                    item_code=weapon_code
                )
                equip_packet = PacketFactory.create_packet(
                    packet_id=PacketList.EQUIPMENT,
                    error_code=1,
                    target_class=target_branch,
                    new_loadout=u.inventory.equipment.loadout[target_branch]
                    )

                await u.send(equip_packet.build())
            else:
                unsuitable_packet = PacketFactory.create_packet(
                    packet_id=PacketList.EQUIPMENT,
                    error_code=EquipmentError.INVALID_BRANCH
                )
                await u.send(unsuitable_packet.build())
