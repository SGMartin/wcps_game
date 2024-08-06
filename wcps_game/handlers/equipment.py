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

        # Determine if the item is being equipped or unequipped
        is_item_equip = not bool(int(self.get_block(0)))
        target_branch = int(self.get_block(1))
        alt_target_slot = int(self.get_block(3))
        weapon_code = self.get_block(4)
        target_slot = int(self.get_block(5))

        item_database = ItemDatabase()

        if not u.authorized:
            return

        if target_slot >= MAX_WEAPONS_SLOTS:
            return

        if target_branch >= MAX_CLASSES:
            await u.disconnect()
            return

        if len(weapon_code) != 4:
            return

        if not item_database.item_exists(code=weapon_code):
            return  # Item does not exist

        # Let admins use inactive items
        if not item_database.is_active(weapon_code) and u.rights < 3:
            await u.disconnect()  # Potential cheater. Log?

        if not u.inventory.has_item(weapon_code) and weapon_code not in DefaultWeapon.DEFAULTS:
            await u.disconnect()  # Potential cheater/scripter. Log?

        # Check if the item is already equipped in the target branch
        equipped_in_slot = u.inventory.equipment.is_equipped_in_class(
            target_class=target_branch, weapon=weapon_code
        )

        if not is_item_equip:  # Unequipping the item
            if equipped_in_slot >= 0:
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

        if equipped_in_slot >= 0:
            # Item is already equipped
            already_equipped_packet = PacketFactory.create_packet(
                packet_id=PacketList.EQUIPMENT,
                error_code=EquipmentError.ALREADY_EQUIPPED
            )
            await u.send(already_equipped_packet.build())
            return

        # Final check: Can the weapon be placed in the target slot?
        valid_codes_for_slot = BranchSlotCodes[target_branch][target_slot]
        weapon_subtype = weapon_code[1]

        if weapon_subtype in valid_codes_for_slot:
            # Perform the actual equipment
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
            # Weapon cannot be placed in the target slot
            unsuitable_packet = PacketFactory.create_packet(
                packet_id=PacketList.EQUIPMENT,
                error_code=EquipmentError.INVALID_BRANCH
            )
            await u.send(unsuitable_packet.build())