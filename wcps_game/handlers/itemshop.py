# Buy K1
# 2024-08-06 10:22:22,021 - INFO - IN:: 5083839 30208 1110 DF05 28 -1 1 
# EXTEND M60 3: 2024-08-06 10:22:51,622 - INFO - IN:: 5113446 30208 1110 DH01 40 -1 0 
# EXTEND m60 7: 2024-08-06 10:22:51,622 - INFO - IN:: 5113446 30208 1110 DH01 40 -1 1
# CROSSHAIR: 2024-08-06 10:23:29,306 - INFO - IN:: 5151138 30208 1110 CC06 11 -1 1 
# K/D RESET 2024-08-06 10:23:46,673 - INFO - IN:: 5168509 30208 1110 CB03 5 -1 0  

from typing import TYPE_CHECKING
import time
import logging

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

import wcps_game.database as db
from wcps_game.client.items import ItemDatabase
from wcps_game.game.constants import ItemAction, LeaseDays, MAX_ITEMS, Premium, get_level_for_exp
from wcps_game.handlers.packet_handler import PacketHandler

from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.error_codes import ItemShopError


class ItemShopHandler(PacketHandler):
    async def process(self, user: "User") -> None:
        
        action_type = int(self.get_block(0))
        item_code = self.get_block(1)
        db_id = self.get_block(2)  # I believe this is unused in CP1 ???
        lease_option = int(self.get_block(4))

        item_database = ItemDatabase()

        valid_lease = [
            LeaseDays.DAYS_3,
            LeaseDays.DAYS_7,
            LeaseDays.DAYS_15,
            LeaseDays.DAYS_30,
            LeaseDays.DAYS_90
            ]

        lease_in_days = {
            LeaseDays.DAYS_3: 3,
            LeaseDays.DAYS_7: 7,
            LeaseDays.DAYS_15: 15,
            LeaseDays.DAYS_30: 30,
            LeaseDays.DAYS_90: 90
        }

        valid_actions = [ItemAction.BUY, ItemAction.REMOVE, ItemAction.USE]    

        if action_type not in valid_actions:
            return

        if len(item_code) != 4:
            return
        if not item_database.item_exists(item_code):
            await user.disconnect()  # TODO: log probable cheater

        if not item_database.is_active(item_code) and user.rights < 3:
            await user.disconnect()  # TODO: log probable cheater

        if action_type == ItemAction.BUY:

            if lease_option not in valid_lease:
                await user.disconnect()  # TODO: log probable cheater

            if not item_database.is_buyable(item_code):
                cannot_be_bought = PacketFactory.create_packet(
                    packet_id=PacketList.ITEMSHOP,
                    error_code=ItemShopError.CANNOT_BE_BOUGHT
                )
                await user.send(cannot_be_bought.build())
                return

            if len(user.inventory.item_list) >= MAX_ITEMS:
                max_item_error = PacketFactory.create_packet(
                    packet_id=PacketList.ITEMSHOP,
                    error_code=ItemShopError.INVENTORY_FULL
                )
                await user.send(max_item_error.build())
                return

            if item_database.requires_premium(item_code) and user.premium == Premium.F2P:
                need_premium = PacketFactory.create_packet(
                    packet_id=PacketList.ITEMSHOP,
                    error_code=ItemShopError.PREMIUM_ONLY
                )
                await user.send(need_premium.build())
                return

            if item_database.get_required_level(item_code) > get_level_for_exp(user.xp):
                low_level = PacketFactory.create_packet(
                    packet_id=PacketList.ITEMSHOP,
                    error_code=ItemShopError.LEVEL_UNSUITABLE
                )
                await user.send(low_level.buil())
                return
            
            # Do not let premium gold users buy 5th slot as in the original game
            if user.premium == Premium.GOLD and item_code == "CA01":  # 5th slot
                cannot_buy_slot = PacketFactory.create_packet(
                    packet_id=PacketList.ITEMSHOP,
                    error_code=ItemShopError.SLOT5_FREE_GOLD
                )
                await user.send(cannot_buy_slot.build())
                return

            this_weapon_cost = item_database.get_weapon_costs(item_code)[lease_option]

            if this_weapon_cost == -1:  # player chose a leasing time not available for weapon
                cannot_be_bought = PacketFactory.create_packet(
                    packet_id=PacketList.ITEMSHOP,
                    error_code=ItemShopError.CANNOT_BE_BOUGHT
                )
                await user.send(cannot_be_bought.build())
                return

            money_left = user.money - this_weapon_cost

            if money_left < 0:
                no_money = PacketFactory.create_packet(
                    packet_id=PacketList.ITEMSHOP,
                    error_code=ItemShopError.NOT_ENOUGH_MONEY
                )
                await user.send(no_money.build())
                return

            # HERE GOES THE BUYING SCHEDULE
            lease_seconds = lease_in_days[lease_option] * 24 * 60 * 60  # h/min/s
            already_has_item = user.inventory.has_item(item_code)

            if not already_has_item:
                can_update = await user.inventory.add_item(
                    item_code=item_code,
                    start_date=int(time.time()),
                    price=this_weapon_cost,
                    lease_seconds=lease_seconds
                    )

                if can_update:
                    # Update user money
                    await user.update_money(new_money=money_left)

                    new_item_packet = PacketFactory.create_packet(
                        packet_id=PacketList.ITEMSHOP,
                        error_code=1,
                        user=user
                    )
                    await user.send(new_item_packet.build())
                else:
                    error_packet = PacketFactory.create_packet(
                        packet_id=PacketList.ITEMSHOP,
                        error_code=ItemShopError.CANNOT_BE_BOUGHT
                    )   
                    await user.send(error_packet.build())
            else:
                # add time to the leasing
                can_update = await db.extend_leasing_time(
                    username=user.username,
                    item_code=item_code,
                    leasing_time=lease_seconds
                )

                if can_update:
                    await user.inventory.extend_item_duration(
                        item_code=item_code,
                        seconds_to_add=lease_seconds
                        )

                    # Update user money
                    await user.update_money(new_money=money_left)

                    new_item_packet = PacketFactory.create_packet(
                        packet_id=PacketList.ITEMSHOP,
                        error_code=1,
                        user=user
                    )
                    await user.send(new_item_packet.build())
                else:
                    error_packet = PacketFactory.create_packet(
                        packet_id=PacketList.ITEMSHOP,
                        error_code=ItemShopError.CANNOT_BE_BOUGHT
                    )         
                    await user.send(error_packet.build())

        elif action_type == ItemAction.USE:
            # 2024-08-06 16:18:19,706 - INFO - IN:: 21177118 30208 1111 CB03 5 3 -1 
            # KD RESET
            # In CP1 PF20, only K/D reset uses this by default. Let's implement it
            if item_code == "CB03":
                await user.stats.reset_kills_deaths()
                await user.inventory.remove_item(item_to_remove=item_code)
                use_packet = PacketFactory.create_packet(
                    packet_id=PacketList.USEITEM,
                    error_code=1,
                    user=user,
                    item_px=item_code
                )
                await user.send(use_packet.build())
            else:
                logging.warning(f"Unknown action for item {item_code}")
        elif action_type == ItemAction.REMOVE:
            logging.warning("CP1 removal item??")

