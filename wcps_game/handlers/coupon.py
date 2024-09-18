from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wcps_game.game.game_server import User

from wcps_game.handlers.packet_handler import PacketHandler
from wcps_game.packets.packet_list import PacketList
from wcps_game.packets.packet_factory import PacketFactory
from wcps_game.packets.error_codes import CouponError


class CouponHandler(PacketHandler):
    async def process(self, user: "User"):
        if user.authorized:
            # This is a basic implementation to aid testers with the wep. system
            # TODO: This can be improved to award items and other stuff
            input_code = self.get_block(0)

            if input_code.lower() == "salmonchurch":
                new_balance = user.money + 50000

                await user.update_money(new_money=new_balance)

                award_packet = PacketFactory.create_packet(
                    packet_id=PacketList.DO_COUPON,
                    error_code=CouponError.SUCCESS,
                    awarded_dinars=new_balance
                )
                await user.send(award_packet.build())
            else:
                error_packet = PacketFactory.create_packet(
                    packet_id=PacketList.DO_COUPON,
                    error_code=CouponError.INCORRECT_CODE,
                    awarded_dinars=user.money
                )
                await user.send(error_packet.build())
